#!/usr/bin/python
# vim:fileencoding=UTF-8

from common import CURRENT_VERSION

import urllib
import http.cookiejar as cookielib
import re
import time
import sys
import logging
from xml.sax.saxutils import unescape as unescapeHTML
from pprint import pprint, pformat

from pyquery import PyQuery

LOGIN_URL = 'https://p.eagate.573.jp/gate/p/login.html'

class EaGate(object):
  def __init__(self, path_to_cookie):
    self.__kid = ''
    self.__password = ''
    self.__otp = ''
    self.__cj = cookielib.MozillaCookieJar(path_to_cookie)
    self.__opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.__cj))
    re_remove_except_number = re.compile(r'\D')
    self._convert_to_number = lambda s: int(re_remove_except_number.sub(u'', s))

  def _get_pyquery(self, raw_html):
    return PyQuery(raw_html.decode('cp932'))

  def set_account(self, kid, password = '', otp = ''):
    self.__kid = kid
    self.__password = password
    self.__otp = otp


  def login(self):
    """成功したらTrueを返す"""

    try: # ロード時のエラーを無視
      self.__cj.load()
    except:
      pass

    # クッキーを食べる
    r = self.__opener.open(LOGIN_URL)
    r.close()
    if 'mypage' in r.geturl(): # すでにログイン済み？
      return True

    # ログインデータ送信
    query_args = { 'KID': self.__kid, 'pass': self.__password, 'OTP': self.__otp }
    encoded_args = urllib.parse.urlencode(query_args).encode('utf-8')
    r = self.__opener.open(LOGIN_URL, encoded_args)
    r.close()
    if 'mypage' not in r.geturl():
      return False

    self.__cj.save()
    return True

  def get_status(self):
    with self.__opener.open('http://p.eagate.573.jp/game/2dx/%d/p/djdata/status.html' % CURRENT_VERSION) as r:
      doc = self._get_pyquery(r.read())

    status = {}

    # 指定したテキストを持つth要素の次のtd要素のテキストを取ってくる
    get_td_text = lambda th_text: doc('th:contains("%s")' % th_text).parent()('td').text()
    status['dj_name'] = get_td_text('DJ NAME')
    status['area'] = get_td_text('所属都道府県')
    status['home'] = get_td_text('所属店舗')
    status['iidx_id'] = get_td_text('IIDX ID')
    status['play_count'] = get_td_text('プレー回数')

    # DJ Point
    status['dj_point'], status['dj_point_sp'], status['dj_point_dp'] = [PyQuery(elem).text() for elem in doc('td.point:contains("pt.")')]

    # 段位認定
    status['class_sp'], status['class_dp'] = [PyQuery(elem).text() for elem in filter(lambda elem: 'pt.' not in elem.text, doc('td.point'))]

    return status

  def _music_list_generator(self, list_number):
    MUSIC_LIST_URL = 'http://p.eagate.573.jp/game/2dx/%d/p/djdata/music.html?list={0}&play_style=0&s=1&page={1}' % CURRENT_VERSION
    page = 1
    while True:
      with self.__opener.open(MUSIC_LIST_URL.format(list_number, page)) as r:
        doc = self._get_pyquery(r.read())
      for minfo in doc('.music_info'):
        yield 'http://p.eagate.573.jp' + PyQuery(minfo).attr('href')
      if doc('a:contains("NEXT")'):
        page += 1
      else:
        return

  def get_music_info(self):
    #MUSIC_INFO_URL = 'http://p.eagate.573.jp/game/2dx/%d/p/djdata/music_info.html?index={0}' % CURRENT_VERSION

    music_info = []

    # まずシリーズのリストページを開く
    first_time = True

    for list_number in range(0, CURRENT_VERSION):
      self._music_list_generator(list_number)
      #music_info.htmlで各曲の詳細を取得
      for url in self._music_list_generator(list_number):
        if not first_time:
          time.sleep(0.2)
        with self.__opener.open(url) as r:
          if 'error01.html' in r.geturl():
            logging.debug(u'エラーページに飛ばされました')
            break
          info = self._parse_music_info(r.read())
        info['version'] = list_number
        music_info.append(info)
        logging.debug(pformat(info))
        first_time = False

    return music_info

  def _parse_music_info(self, raw_html):

    info = {}

    doc = self._get_pyquery(raw_html)

    # 曲名、ジャンル、アーティスト
    tag = [unescapeHTML(line).strip() for line in doc(".music_info_td").html().split('<br />')]
    info['name'], info['genre'], info['artist'] = tag

    pprint(info)
    # 選曲数
    text_list = doc("p:contains('選曲数')")
    info['play_count_sp'], info['play_count_dp'], *_ = list(map(lambda elem: int(re.sub(r'^.*(\d+).*', r'\1', elem.text)), text_list)) + [None]

    # クリアランプ
    info['clear_lamp_spn'], info['clear_lamp_sph'], info['clear_lamp_spa'], info['clear_lamp_dpn'], info['clear_lamp_dph'], info['clear_lamp_dpa'] = \
        [img.attr('alt') for img in filter(lambda img: 'clflg' in img.attr('src'), map(PyQuery, doc("img")))]

    # DJ LEVEL
    info['dj_level_spn'], info['dj_level_sph'], info['dj_level_spa'], info['dj_level_dpn'], info['dj_level_dph'], info['dj_level_dpa'], *_ = \
        [img.attr('alt') for img in filter(lambda img: 'clflg' not in img.attr('src'), map(PyQuery, doc("img")))] + [None] * 6

    # Score
    td_list = [td.text() for td in map(PyQuery, doc('th:contains("SCORE(Pgreat/Great)")').parent()('td'))]
    info['ex_score_spn'], info['pgreat_spn'], info['great_spn'] = self._extract_score(td_list[0])
    info['ex_score_sph'], info['pgreat_sph'], info['great_sph'] = self._extract_score(td_list[1])
    info['ex_score_spa'], info['pgreat_spa'], info['great_spa'] = self._extract_score(td_list[2])
    info['ex_score_dpn'], info['pgreat_dpn'], info['great_dpn'] = self._extract_score(td_list[3])
    info['ex_score_dph'], info['pgreat_dph'], info['great_dph'] = self._extract_score(td_list[4])
    info['ex_score_dpa'], info['pgreat_dpa'], info['great_dpa'] = self._extract_score(td_list[5])

    # Miss count
    td_list = [td.text() for td in map(PyQuery, doc('th:contains("MISS COUNT")').parent()('td'))]
    info['miss_count_spn'] = self._extract_miss_count(td_list[0])
    info['miss_count_sph'] = self._extract_miss_count(td_list[1])
    info['miss_count_spa'] = self._extract_miss_count(td_list[2])
    info['miss_count_dpn'] = self._extract_miss_count(td_list[3])
    info['miss_count_dph'] = self._extract_miss_count(td_list[4])
    info['miss_count_dpa'] = self._extract_miss_count(td_list[5])

    return info

  def _extract_score(self, text):
    re_score = re.compile(r'(\d+)\((\d+)\/(\d+)\)')
    m = re_score.match(text)
    if m == None:
      return None, None, None
    ex_score = int(m.group(1))
    pgreat = int(m.group(2))
    great = int(m.group(3))
    return ex_score, pgreat, great

  def _extract_miss_count(self, text):
    re_miss_count = re.compile(r'\d+')
    m = re_miss_count.match(text)
    if m == None:
      return None
    return int(m.group(0))
