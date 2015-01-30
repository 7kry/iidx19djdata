#! /usr/bin/python3
# vim:fileencoding=UTF-8

import csv
import sys
from pprint import pprint

if len(sys.argv) < 2:
  sys.stderr.write("USAGE %s /path/to/music-info.csv [/path/to/iidxac22.score.txt]\n" % sys.argv[0])
  sys.exit(1)

with open(sys.argv[1]) as fp:
  with open(sys.argv[2] if len(sys.argv) > 2 else 'iidxac22.score.txt', 'w', encoding = 'utf_16') as wfp:
    reader = csv.reader(fp)
    columns = next(reader)
    for music in reader:
      data = dict(zip(columns, [elem if elem is not '' else '-' for elem in music]))
      wfp.write("\t".join([
        data['name'],
        data['genre'],
        data['artist'],
        data['clear_lamp_spn'],
        data['clear_lamp_sph'],
        data['clear_lamp_spa'],
        "%s(%s/%s)" % (data['ex_score_spn'], data['pgreat_spn'], data['great_spn']),
        "%s(%s/%s)" % (data['ex_score_sph'], data['pgreat_sph'], data['great_sph']),
        "%s(%s/%s)" % (data['ex_score_spa'], data['pgreat_spa'], data['great_spa']),
        data['miss_count_spn'],
        data['miss_count_sph'],
        data['miss_count_spa'],
        data['clear_lamp_dpn'],
        data['clear_lamp_dph'],
        data['clear_lamp_dpa'],
        "%s(%s/%s)" % (data['ex_score_dpn'], data['pgreat_dpn'], data['great_dpn']),
        "%s(%s/%s)" % (data['ex_score_dph'], data['pgreat_dph'], data['great_dph']),
        "%s(%s/%s)" % (data['ex_score_dpa'], data['pgreat_dpa'], data['great_dpa']),
        data['miss_count_dpn'],
        data['miss_count_dph'],
        data['miss_count_dpa'],
      ]) + '\r\n')
