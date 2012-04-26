#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib
import urllib2
import cookielib
import re
import time
import sys
import logging

import BeautifulSoup

LOGIN_URL = 'https://p.eagate.573.jp/gate/p/login.html'

class EaGate(object):
    def __init__(self):
        self._kid = ''
        self._password = ''
        self._otp = ''
        self._cj = cookielib.MozillaCookieJar('cookies.txt')
        self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self._cj))
        re_remove_except_number = re.compile(ur'\D')
        self._convert_to_number = lambda s: int(re_remove_except_number.sub(u'', s))

    def set_account(self, kid, password, otp = ''):
        self._kid = kid
        self._password = password
        self._otp = otp


    def login(self):
        ur"""成功したらTrueを返す"""

        try: # ロード時のエラーを無視
            self._cj.load()
        except:
            pass

        # クッキーを食べる
        r = self._opener.open(LOGIN_URL)
        r.close()
        if 'done_login' in r.geturl(): # すでにログイン済み？
            return True

        # ログインデータ送信
        query_args = { 'KID': self._kid, 'pass': self._password, 'OTP': self._otp }
        encoded_args = urllib.urlencode(query_args)
        r = self._opener.open(LOGIN_URL, encoded_args)
        r.close()
        if 'done_login' not in r.geturl():
            return False

        self._cj.save()
        return True

    def get_status(self):
        r = self._opener.open('http://p.eagate.573.jp/game/2dx/19/p/djdata/status.html')
        raw_html = r.read()
        r.close()

        bs = BeautifulSoup.BeautifulSoup(raw_html)

        status = {}

        # 指定したテキストを持つth要素の次のtd要素のテキストを取ってくる
        get_td_text = lambda th_text: bs.find(
            lambda tag: tag.name == u'th' and tag.text == th_text).findNextSibling(u'td').text
        status['dj_name'] = get_td_text(u'DJ Name')
        status['area'] = get_td_text(u'所属都道府県')
        status['iidx_id'] = get_td_text(u'IIDX ID')

        # DJ Point
        first_text = bs.find(lambda tag: tag.name == u'th' and tag.text == u'DJ POINT')
        tds = first_text.findNextSiblings(u'td')
        status['dj_point'] = self._convert_to_number(tds[1].text)
        status['dj_point_sp'] = self._convert_to_number(tds[3].text)
        status['dj_point_dp'] = self._convert_to_number(tds[5].text)

        # 段位認定
        first_text = bs.find(lambda tag: tag.name == u'th' and tag.text == u'段位認定')
        tds = first_text.findNextSiblings(u'td')
        status['class_sp'] = tds[1].text
        status['class_dp'] = tds[3].text

        # プレー回数
        first_text = bs.find(lambda tag: tag.name == u'th' and tag.text == u'プレー回数')
        tds = first_text.findNextSiblings(u'td')
        status['play_count'] = self._convert_to_number(tds[1].text)
        status['play_count_sp'] = self._convert_to_number(tds[3].text)
        status['play_count_dp'] = self._convert_to_number(tds[5].text)

        return status

    def get_music_info(self):
        MUSIC_LIST_URL = 'http://p.eagate.573.jp/game/2dx/19/p/djdata/music.html?list={0}&s=1'
        MUSIC_INFO_URL = 'http://p.eagate.573.jp/game/2dx/19/p/djdata/music_info.html?index={0}'

        music_info = []

        # まずシリーズのリストページを開く
        first_time = True
        for list_number in xrange(0, 19):
            r = self._opener.open(MUSIC_LIST_URL.format(list_number))
            html = r.read()
            r.close()
            #music_info.htmlで各曲の詳細を取得
            for index_number in xrange(100):
                if not first_time:
                    logging.debug(u'待機中...')
                    time.sleep(15)
                logging.debug(u'取得中... list_number={0} index_number={1}'.format(list_number, index_number))
                r = self._opener.open(MUSIC_INFO_URL.format(index_number))
                raw_html = r.read()
                r.close()
                if 'error01.html' in r.geturl():
                    logging.debug(u'エラーページに飛ばされました')
                    break
                info = self._parse_music_info(raw_html)
                info['version'] = list_number
                music_info.append(info)
                first_time = False


        return music_info

    def _parse_music_info(self, raw_html):

        info = {}

        bs = BeautifulSoup.BeautifulSoup(raw_html)

        # 曲名、ジャンル、アーティスト
        tag = bs.find(u'td', u'music_info_td')
        info['name'] = tag.contents[0].strip()
        info['genre'] = tag.contents[2].strip()
        info['artist'] = tag.contents[4].strip()

        # 選曲数
        text_list = bs.findAll(text=re.compile(ur'選曲数\s*\d+回'))
        info['play_count_sp'] = self._convert_to_number(text_list[0])
        info['play_count_dp'] = self._convert_to_number(text_list[1])

        # クリアランプ
        re_clflg = re.compile(ur'clflg(\d)\.gif')
        img_list = bs.findAll(u'img', {'src': re_clflg})
        extract_from_img = lambda img: int(re_clflg.search(img.attrMap['src']).group(1))
        info['clear_lamp_spn'] = extract_from_img(img_list[0])
        info['clear_lamp_sph'] = extract_from_img(img_list[1])
        info['clear_lamp_spa'] = extract_from_img(img_list[2])
        info['clear_lamp_dpn'] = extract_from_img(img_list[3])
        info['clear_lamp_dph'] = extract_from_img(img_list[4])
        info['clear_lamp_dpa'] = extract_from_img(img_list[5])

        # DJ LEVEL
        th_list = bs.findAll(lambda tag: tag.name == u'th' and tag.text == u'DJ LEVEL')
        td_list = th_list[0].findNextSiblings(u'td')
        info['dj_level_spn'] = self._extract_dj_level(td_list[0])
        info['dj_level_sph'] = self._extract_dj_level(td_list[1])
        info['dj_level_spa'] = self._extract_dj_level(td_list[2])
        td_list = th_list[1].findNextSiblings(u'td')
        info['dj_level_dpn'] = self._extract_dj_level(td_list[0])
        info['dj_level_dph'] = self._extract_dj_level(td_list[1])
        info['dj_level_dpa'] = self._extract_dj_level(td_list[2])

        # Score
        th_list = bs.findAll(lambda tag: tag.name == u'th' and tag.text == u'SCORE(Pgreat/Great)')
        td_list = th_list[0].findNextSiblings(u'td')
        info['ex_score_spn'], info['pgreat_spn'], info['great_spn'] = self._extract_score(td_list[0])
        info['ex_score_sph'], info['pgreat_sph'], info['great_sph'] = self._extract_score(td_list[1])
        info['ex_score_spa'], info['pgreat_spa'], info['great_spa'] = self._extract_score(td_list[2])
        td_list = th_list[1].findNextSiblings(u'td')
        info['ex_score_dpn'], info['pgreat_dpn'], info['great_dpn'] = self._extract_score(td_list[0])
        info['ex_score_dph'], info['pgreat_dph'], info['great_dph'] = self._extract_score(td_list[1])
        info['ex_score_dpa'], info['pgreat_dpa'], info['great_dpa'] = self._extract_score(td_list[2])

        # Miss count
        th_list = bs.findAll(lambda tag: tag.name == u'th' and tag.text == u'MISS COUNT')
        td_list = th_list[0].findNextSiblings(u'td')
        info['miss_count_spn'] = self._extract_miss_count(td_list[0])
        info['miss_count_sph'] = self._extract_miss_count(td_list[1])
        info['miss_count_spa'] = self._extract_miss_count(td_list[2])
        td_list = th_list[1].findNextSiblings(u'td')
        info['miss_count_dpn'] = self._extract_miss_count(td_list[0])
        info['miss_count_dph'] = self._extract_miss_count(td_list[1])
        info['miss_count_dpa'] = self._extract_miss_count(td_list[2])

        return info

    def _extract_dj_level(self, td):
        img = td.find(u'img')
        if img == None:
            return None
        if u'alt' not in img.attrMap:
            return None
        return img.attrMap[u'alt']

    def _extract_score(self, td):
        re_score = re.compile(ur'(\d+)\((\d+)\/(\d+)\)')
        m = re_score.match(td.text)
        if m == None:
            return None, None, None
        ex_score = int(m.group(1))
        pgreat = int(m.group(2))
        great = int(m.group(3))
        return ex_score, pgreat, great

    def _extract_miss_count(self, td):
        re_miss_count = re.compile(ur'\d+')
        m = re_miss_count.match(td.text)
        if m == None:
            return None
        return int(m.group(0))

def main():
    f = open('account.txt')
    line = f.readline()
    list = line.split()
    kid, password = list[0:2]

    eagate = EaGate()
    eagate.set_account(kid, password)
    if eagate.login() == False:
        print u'ログインに失敗しました'
        return
    eagate.get_music_info()

if __name__ == '__main__':
    main()
