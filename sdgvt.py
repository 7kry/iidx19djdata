# vim:fileencoding=UTF-8

import urllib
import http.cookiejar as cookielib
from xml.etree import ElementTree

from eagate import CURRENT_VERSION

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
      }).encode('utf-8')
    with self.__opener.open(BASE_URL + '/login.php', query) as res:
      xmlstr = res.read().decode('shift_jis')
      if not ElementTree.fromstring(xmlstr).find('userid').text:
        raise Exception('Failed to login to SDGVT.')
    self.__cj.save()
