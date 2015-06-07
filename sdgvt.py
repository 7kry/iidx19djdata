# vim:fileencoding=UTF-8

import logging
from   functools import reduce
import http.cookiejar as cookielib
import io
import urllib
from   xml.etree import ElementTree
from   zipfile import ZipFile

from common import CURRENT_VERSION

BASE_URL = 'http://felice.dip.jp/iidxac%d/' % CURRENT_VERSION

class SDGVT:
  CLEARLAMP = {
    "FULL COMBO"   : 7,
    "EX HARD CLEAR": 6,
    "HARD CLEAR"   : 5,
    "ASSIST CLEAR" : 4,
    "EASY CLEAR"   : 3,
    "FAILED"       : 2,
    "CLEAR"        : 1,
    "NO PLAY"      : 0,
  }

  LAMPALIAS = {
    "FULL COMBO"   : "FC",
    "EX HARD CLEAR": "EXHARD",
    "HARD CLEAR"   : "HARD",
    "ASSIST CLEAR" : "ASSIST",
    "EASY CLEAR"   : "EASY",
    "FAILED"       : "FAILED",
    "CLEAR"        : "CLEAR",
    "NO PLAY"      : "NOPLAY",
  }

  def __init__(self, username, password, path_to_cookie):
    self.__username = username
    self.__password = password
    self.__cj = cookielib.MozillaCookieJar(path_to_cookie)
    self.__opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.__cj))

  def login(self):
    # トップページ
    self.__opener.open(BASE_URL).close()

    # ログイン
    query = urllib.parse.urlencode({
        'userid'  : self.__username,
        'password': self.__password,
      }).encode('ascii')
    with self.__opener.open(BASE_URL + 'login.php', query) as res:
      xmlstr = res.read().decode('shift_jis')
      if not ElementTree.fromstring(xmlstr).find('userid').text:
        raise Exception('Failed to login to SDGVT.')
    self.__cj.save()

  def upload(self, music_info):
    # 楽曲IDリストの取得
    songid = dict(map(lambda song: (song.find('songname').text, song.find('songid').text), ElementTree.fromstring(self.__opener.open(BASE_URL + 'getsongdic.php').read().decode('cp932')).findall('song')))

    # 登録済みスコアを取得
    registered = {}
    for version in range(1, CURRENT_VERSION + 1):
      for data in ElementTree.fromstring(self.__opener.open(BASE_URL + 'getscoredata.php', urllib.parse.urlencode({'userid': self.__username, 'version': version}).encode('ascii')).read().decode('cp932')).findall('data'):
        registered[(data.find('songname').text, data.find('playstyle').text, data.find('mode').text)] = \
            (data.find('clearlamp').text, data.find('exscore').text, data.find('misscount').text)

    for item in music_info:
      itemid = None
      try:
        itemid = songid[item['name']]
      except KeyError:
        logging.error('`{name}\' not found...'.format(name = item['name']))
        continue
      self._upload_song(registered, item['name'], itemid, 'sp', 'N', item['ex_score_spn'], item['clear_lamp_spn'], item['miss_count_spn'])
      self._upload_song(registered, item['name'], itemid, 'sp', 'H', item['ex_score_sph'], item['clear_lamp_sph'], item['miss_count_sph'])
      self._upload_song(registered, item['name'], itemid, 'sp', 'A', item['ex_score_spa'], item['clear_lamp_spa'], item['miss_count_spa'])
      self._upload_song(registered, item['name'], itemid, 'dp', 'N', item['ex_score_dpn'], item['clear_lamp_dpn'], item['miss_count_dpn'])
      self._upload_song(registered, item['name'], itemid, 'dp', 'H', item['ex_score_dph'], item['clear_lamp_dph'], item['miss_count_dph'])
      self._upload_song(registered, item['name'], itemid, 'dp', 'A', item['ex_score_dpa'], item['clear_lamp_dpa'], item['miss_count_dpa'])

  def _upload_song(self, registered, songname, songid, sp_or_dp, nha, exscore, lamp, misscount):
    key = (songname, sp_or_dp, nha)
    if key in registered and registered[key] == (SDGVT.LAMPALIAS[lamp], exscore or '0', misscount or '-'):
      return
    query = {
      "songid"   : songid,
      "playstyle": sp_or_dp,
      "mode"     : nha,
      "exscore"  : exscore,
      "clearlamp": SDGVT.CLEARLAMP[lamp],
      "userid"   : self.__username,
    }
    if misscount:
      query['misscount'] = misscount
    with self.__opener.open(BASE_URL + 'updatescoredata.php', urllib.parse.urlencode(query).encode('ascii')) as r:
      result = ElementTree.fromstring(r.read().decode('cp932')).text
      logging.info("%s[%s]: %s" % (songname, sp_or_dp.upper() + nha, result))
