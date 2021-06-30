from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.request import urlopen
import argparse
import sys

# ================================

FLAGS = argparse.ArgumentParser(
  description='Fetches options data from Yahoo Finance.')
FLAGS.add_argument(
  '--s',
  help='The stock symbol',
  type=str)
FLAGS.add_argument(
  '--y',
  help='The year',
  type=int)
FLAGS.add_argument(
  '--m',
  help='The month as a number from 1 to 12',
  type=int)
FLAGS.add_argument(
  '--d',
  help='The day',
  type=int)
FLAGS.add_argument(
  '--h',
  help='Show headings',
  action='store_true')

# ================================

OPTIONS_URL = 'https://finance.yahoo.com/quote/%s/options?date=%d'

HEADINGS = [
  'Type',
  'ID',
  'Last Trade',
  'Strike',
  'Price',
  'Bid',
  'Ask',
  'Chg',
  '% Chg',
  'Vol',
  'OI',
  'IV',
]

# ================================

class OptionsParser(HTMLParser):

  def __init__(self):
    HTMLParser.__init__(self)
    self._in_tr = False
    self._items = []
    self._cur_item = None
    self._cur_type = None

  def handle_starttag(self, tag, attrs):
    if tag == 'table':
      if HasClass(attrs, lambda cls: cls.startswith('calls')):
        self._cur_type = 'CALL'
      elif HasClass(attrs, lambda cls: cls.startswith('puts')):
        self._cur_type = 'PUT'

    if tag == 'tr':
      if HasClass(attrs, lambda cls: cls.startswith('data-row')):
        self._in_tr = True
        self._cur_item = [self._cur_type]

  def handle_endtag(self, tag):
    if tag == 'tr' and self._in_tr:
      self._in_tr = False
      self._items.append(self._cur_item)

  def handle_data(self, data):
    data = data.strip()
    if self._in_tr and data:
      self._cur_item.append(str(data))

# ================================

def HasClass(attrs, fn):
  for attr in attrs:
    if attr[0] == 'class' and fn(attr[1]):
      return True
  return False


def Log(stream, text):
  stream.write(text)
  stream.write('\n')
  stream.flush()


def OpenUrl(url):
  try:
    fp = urlopen(url)
    html = fp.read()
    fp.close()
    return html
  except:
    Log(sys.stderr, '[%s] %s' % (sys.exc_info()[1], url))
  return False


def ToLine(item, skip=[]):
  ans = ''
  first = True
  for i, v in enumerate(item):
    if i not in skip:
      if not first:
        ans += '\t'
      ans += v
    first = False
  return ans


def Dump(items, headings=False, skip=[]):
  if headings:
    Log(sys.stdout, ToLine(HEADINGS, skip))
  for item in items:
    Log(sys.stdout, ToLine(item, skip))


def main():
  args = FLAGS.parse_args()

  if args.s is None:
    Log(sys.stderr, 'Please enter a symbol.')
    return

  d = datetime.today()
  d = d.replace(hour=0, minute=0, second=0, tzinfo=timezone.utc)
  year = args.y if args.y is not None else d.year
  month = args.m if args.m is not None else d.month
  day = args.d if args.d is not None else d.day
  d = d.replace(year, month, day)
  t = int(d.timestamp())

  url = OPTIONS_URL % (args.s, t)
  html = OpenUrl(url)
  parser = OptionsParser()
  parser.feed(str(html))

  if not parser._items:
    Log(sys.stderr, ('No data for this date: %s' % d.strftime('%Y-%m-%d')))
    return

  # skip contract ID
  Dump(parser._items, headings=args.h, skip=[1])

# ================================

if __name__ == '__main__':
  main()
