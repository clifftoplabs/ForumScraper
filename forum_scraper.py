"""
Forum Scraper

Usage:
  forum_scraper -f <urls_filename> | -u <csv_urls> [-v]
  forum_scraper -h | --help

Options:
  -f <urls_filename>, --input-file <urls_filename>  Text file with a forum url per line
  -u <csv_urls>, --csv-urls <csv_urls>              URLs of forums separated by a comma
  -h, --help                                        Show this screen.
  -v                                                Verbose
"""

from docopt import docopt
import logging
from typing import List, AnyStr

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def scrape_forum(url: AnyStr):
  return

def scrape_forums(urls: List[AnyStr]):
  for url in urls:
    scrape_forum(url)

def get_urls(input_file: AnyStr, csv_urls: AnyStr):
  # TODO: Implement reading input for URLs
  logger.info(f" Input File: {input_file} | CSV Urls: {csv_urls}")
  return [
    "https://www.e90post.com/forums/showthread.php?t=1000",
    "https://forums.hexus.net/showthread.php?t=1234"
  ]

def main():
  # Parse the input arguments to get the run options and urls filename or csv
  args = docopt(__doc__, version='Forum Scraper v0.1')

  # Read the list of URLs
  urls = get_urls(args.get("--input-file"), args.get("--csv-urls"))

  # Scrape each forum from the urls
  scrape_forums(urls)

if __name__ == "__main__":
    main()
