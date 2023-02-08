"""
Forum Scraper

Usage:
  forum_scraper (-f <urls_filename> | -u <csv_urls>) [-v]
  forum_scraper -h | --help

Options:
  -f <urls_filename>, --input-file <urls_filename>  Text file with a forum url per line
  -u <csv_urls>, --csv-urls <csv_urls>              URLs of forums separated by a comma
  -h, --help                                        Show this screen.
  -v, --verbose                                     Verbose
"""

from bs4 import BeautifulSoup
from bs4.element import PageElement
from docopt import docopt
from enum import Enum
import http.client as http_client
import logging
from typing import Any, AnyStr, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SoftwareType(Enum):
  CUSTOM = 0
  TABLE_POSTS = 1
  LIST_POSTS = 2

def get_url_contents(url: AnyStr) -> Optional[AnyStr]:
  headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"}

  request_parts = url.split("//")
  endpoint_parts = request_parts[1].split("/")
  domain = endpoint_parts[0]
  endpoint = "/" + "/".join(endpoint_parts[1:])

  conn = http_client.HTTPSConnection(domain)
  conn.request("GET", endpoint, None, headers)
  response = conn.getresponse()

  if response.status == 301:
    return get_url_contents(response.headers.get("Location"))

  if response.status != 200:
    logger.error(f"Unexpected status code {response.status} when accessing url {url}")
    return None

  logger.info(f"Retrieved contents of {url}")
  return response.read()

# TODO: Dry up these functions by using a config to define the search terms
def parse_table_posts_forum(posts_container: PageElement):
  logger.debug(f"Parsing table posts - Element Count: {len(posts_container.contents)}")

def parse_list_posts_forum(posts_container: PageElement):
  logger.debug(f"Parsing list posts - Element Count: {len(posts_container.contents)}")

def parse_forum_with_config(posts_container: PageElement, config: Dict[AnyStr, Any]):
  logger.debug(f"Parsing custom software - Element Count: {len(posts_container.contents)} | Config: {config}")

def scrape_forum(url: AnyStr) -> AnyStr:
  url_contents = get_url_contents(url)
  soup = BeautifulSoup(url_contents, "html.parser")
  posts = soup.find(id="posts")

  software = SoftwareType.CUSTOM
  if posts.name == "ol":
    software = SoftwareType.LIST_POSTS
  if posts.name == "div" and posts.table is not None:
    software = SoftwareType.TABLE_POSTS

  if software == SoftwareType.TABLE_POSTS:
    parse_table_posts_forum(posts)
  elif software == SoftwareType.LIST_POSTS:
    parse_list_posts_forum(posts)
  else:
    # TODO: Support passing in a custom config
    parse_forum_with_config(posts, {})

  return url_contents.decode("utf-8")

def scrape_forums(urls: List[AnyStr], is_debug: bool):
  with open(f"output.txt", "w+") as fp:
    for url in urls:
      contents = scrape_forum(url)
      if is_debug:
        fp.write(contents)

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

  if args.get("--verbose"):
    logger.setLevel(logging.DEBUG)

  # Read the list of URLs
  urls = get_urls(args.get("--input-file"), args.get("--csv-urls"))

  # Scrape each forum from the urls
  scrape_forums(urls, args.get("--verbose"))

if __name__ == "__main__":
    main()
