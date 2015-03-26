# vim:fileencoding=utf-8

import csv

CURRENT_VERSION = 22 # IIDX 22 PENDUAL

FIELDS = [
    'name', 'genre', 'artist', 'version', 'play_count_sp', 'play_count_dp',
    'clear_lamp_spn', 'dj_level_spn', 'ex_score_spn', 'pgreat_spn', 'great_spn', 'miss_count_spn',
    'clear_lamp_sph', 'dj_level_sph', 'ex_score_sph', 'pgreat_sph', 'great_sph', 'miss_count_sph',
    'clear_lamp_spa', 'dj_level_spa', 'ex_score_spa', 'pgreat_spa', 'great_spa', 'miss_count_spa',
    'clear_lamp_dpn', 'dj_level_dpn', 'ex_score_dpn', 'pgreat_dpn', 'great_dpn', 'miss_count_dpn',
    'clear_lamp_dph', 'dj_level_dph', 'ex_score_dph', 'pgreat_dph', 'great_dph', 'miss_count_dph',
    'clear_lamp_dpa', 'dj_level_dpa', 'ex_score_dpa', 'pgreat_dpa', 'great_dpa', 'miss_count_dpa',
]

def save_music_info(fp, music_info):
  writer = csv.DictWriter(fp, FIELDS, lineterminator = '\n')
  writer.writeheader()
  # エンコードして書き出す
  for row in music_info:
    row_encoded = {}
    for key, value in row.items():
      row_encoded[key] = value
    writer.writerow(row_encoded)

def load_music_info(fp):
  reader = csv.reader(fp)
  header = next(reader)
  if header != FIELDS:
    raise Exception('Invalid music-info.csv.')
  return list(map(lambda row: dict(zip(header, row)), reader))
