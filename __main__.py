#!/usr/bin/python
# vim:fileencoding=UTF-8

import argparse
import csv
import sys
import locale
import logging
import tempfile
from getpass import getpass

import common
import eagate
import sdgvt

def fetch(args):
  logging.basicConfig(level = logging.DEBUG)

  kid, password = input("KONAMI ID: "), getpass("Password: ")

  with tempfile.NamedTemporaryFile() as tmp:
    eg = eagate.EaGate(tmp.name)
    eg.set_account(kid, password)
    logging.info('loginning...')
    if eg.login() == False:
        logging.error('Failed to login!')
        return
    logging.info(u'Fetching data...')
    music_info = eg.get_music_info()

  common.save_music_info(open(args.savedest, 'w'), music_info)

  return music_info

def sdgvt_upload(args):
  sdgvt.logging.basicConfig(level = logging.INFO)
  with open(args.path_to_csv) as fp:
    music_info = common.load_music_info(fp)
    with tempfile.NamedTemporaryFile() as tmp:
      session = sdgvt.SDGVT(input('SDGVT Username: '), getpass('Password: '), tmp.name)
      session.login()
      session.upload(music_info)

argparser_root = argparse.ArgumentParser()
argparser_root.set_defaults(func = None)

subparser = argparser_root.add_subparsers()
parser_fetch = subparser.add_parser('fetch', help = 'to Fetch your DJ DATA from e-AMUSEMENT GATE.')
parser_fetch.set_defaults(func = fetch, savedest = 'music-info.csv')
parser_fetch.add_argument('--savedest')

parser_fetch = subparser.add_parser('sdgvt', help = 'to Upload your DJ DATA to IIDX SCORE DATA GRAPHICAL VIEW TOOL.')
parser_fetch.set_defaults(func = sdgvt_upload)
parser_fetch.add_argument('path_to_csv')

args = argparser_root.parse_args()
if args.func:
  args.func(args)
else:
  argparser_root.parse_args(["--help"])
