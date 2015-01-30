#!/usr/bin/python
# vim:fileencoding=UTF-8

import csv
import sys
import locale
import logging
from getpass import getpass

import eagate

def main():
  logging.basicConfig(level = logging.DEBUG)

  kid, password = input("KONAMI ID: "), getpass("Password: ")

  eg = eagate.EaGate()
  eg.set_account(kid, password)
  logging.info('loginning...')
  if eg.login() == False:
      logging.error('Failed to login!')
      return
  logging.info(u'Fetching data...')
  music_info = eg.get_music_info()

  FIELDS = [
      'name', 'genre', 'artist', 'version', 'play_count_sp', 'play_count_dp',
      'clear_lamp_spn', 'dj_level_spn', 'ex_score_spn', 'pgreat_spn', 'great_spn', 'miss_count_spn',
      'clear_lamp_sph', 'dj_level_sph', 'ex_score_sph', 'pgreat_sph', 'great_sph', 'miss_count_sph',
      'clear_lamp_spa', 'dj_level_spa', 'ex_score_spa', 'pgreat_spa', 'great_spa', 'miss_count_spa',
      'clear_lamp_dpn', 'dj_level_dpn', 'ex_score_dpn', 'pgreat_dpn', 'great_dpn', 'miss_count_dpn',
      'clear_lamp_dph', 'dj_level_dph', 'ex_score_dph', 'pgreat_dph', 'great_dph', 'miss_count_dph',
      'clear_lamp_dpa', 'dj_level_dpa', 'ex_score_dpa', 'pgreat_dpa', 'great_dpa', 'miss_count_dpa',
  ]

  with open(u'music-info.csv', 'w') as f:
    writer = csv.DictWriter(f, FIELDS, lineterminator = '\n')
    writer.writeheader()
    # エンコードして書き出す
    for row in music_info:
      row_encoded = {}
      for key, value in row.items():
        row_encoded[key] = value
      writer.writerow(row_encoded)
    logging.info(u'"{0}"に書き出しました'.format(f.name))

if __name__ == '__main__':
  main()
