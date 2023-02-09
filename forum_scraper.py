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
from datetime import datetime
from docopt import docopt
from enum import Enum
import http.client as http_client
import json
import logging
from typing import Any, AnyStr, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("forum_scraper")

class SoftwareType(Enum):
  CUSTOM = 0
  TABLE_POSTS = 1
  LIST_POSTS = 2


class ParserConfig:
  def __init__(
    self,
    posts_container: AnyStr,
    posts: AnyStr,
    post_header: AnyStr,
    post_date: AnyStr,
    post_order: AnyStr,
    post_details: AnyStr,
    post_user_info: AnyStr,
    post_username: AnyStr,
    post_body: AnyStr,
    post_title: AnyStr,
    post_contents: AnyStr,
  ):
    self.posts_container = posts_container
    self.posts = posts
    self.post_header = post_header
    self.post_date = post_date
    self.post_order = post_order
    self.post_details = post_details
    self.post_user_info = post_user_info
    self.post_username = post_username
    self.post_body = post_body
    self.post_title = post_title
    self.post_contents = post_contents


DEFAULT_CONFIGS = {
  "vBulletin 3.8.11": ParserConfig(
    posts_container="#posts",
    posts="table[id]",
    post_header="tr:first-of-type",
    post_date="td:first-of-type",
    post_order="td:nth-of-type(2)",
    post_details="tr:nth-of-type(2)",
    post_user_info="td:first-of-type",
    post_username=".bigusername",
    post_body="td:nth-of-type(2)",
    post_title="div:not([id])",
    post_contents=".thePostItself"
  ),
  "vBulletin 4.2.2": ParserConfig(
    posts_container="#posts",
    posts="li.postcontainer",
    post_header=".posthead",
    post_date=".postdate",
    post_order=".nodecontrols",
    post_details=".postdetails",
    post_user_info=".userinfo",
    post_username=".username",
    post_body=".postbody",
    post_title=".title",
    post_contents=".content"
  ),
}

class ForumPost:
  def __init__(self):
    self.date: Optional[datetime] = None
    # TODO: Promote to user object that is unique by username and collects other user data
    self.username: Optional[AnyStr] = None
    self.title: Optional[AnyStr] = None
    self.contents: Optional[AnyStr] = None
    self.order: Optional[int] = None

  def to_json(self):
    return {
      "date": self.date,
      "user": self.username,
      "title": self.title,
      "contents": self.contents,
      "order": self.order,
    }

class ForumParser:
  def __init__(self, software: SoftwareType, config: ParserConfig):
    self.software = software
    self.config = config
    self.posts: List[ForumPost] = []

  def parse(self, soup: BeautifulSoup):
    posts_container = soup.select_one(self.config.posts_container)
    posts = posts_container.select(self.config.posts)

    logger.debug(f"Parsing {self.software} posts - Post Count: {len(posts)}")
    for post_element in posts:
      self.parse_post(post_element)

  def parse_post(self, post_element: PageElement):
    post = ForumPost()

    post_header = post_element.select_one(self.config.post_header)
    post.date = self.clean_string(post_header.select_one(self.config.post_date))
    post.order = int(self.clean_string(post_header.select_one(self.config.post_order)).replace("#", ""))

    post_details = post_element.select_one(self.config.post_details)
    post_user_info = post_details.select_one(self.config.post_user_info)
    post.username = self.clean_string(post_user_info.select_one(self.config.post_username))
    post_body = post_details.select_one(self.config.post_body)
    post.title = self.clean_string(post_body.select_one(self.config.post_title))
    post.contents = self.clean_string(post_body.select_one(self.config.post_contents))

    self.posts.append(post)

  def clean_string(self, element: PageElement) -> Optional[AnyStr]:
    if element is None:
      return None
    return "".join(element.strings).strip()

  def to_json(self):
    return [post.to_json() for post in self.posts]


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

def scrape_forum(url: AnyStr) -> AnyStr:
  url_contents = get_url_contents(url)
  soup = BeautifulSoup(url_contents, "html.parser")
  software = soup.select_one("meta[name=\"generator\"]").attrs["content"]
  if software not in DEFAULT_CONFIGS:
    # TODO: Enable ability to specify custom config
    return "[]"

  forum_parser = ForumParser(software, DEFAULT_CONFIGS[software])
  forum_parser.parse(soup)

  return json.dumps(forum_parser.to_json(), indent=2)

def scrape_forums(urls: List[AnyStr], is_debug: bool):
  with open(f"output.txt", "w+") as fp:
    for url in urls:
      contents = scrape_forum(url)
      fp.write(contents + "\n\n")

def get_urls(input_file: Optional[AnyStr], csv_urls: Optional[AnyStr]):
  if input_file is not None:
    logger.debug(f"Input File: {input_file}")
    with open(input_file, "r") as fp:
      return [url.strip() for url in fp.readlines()]

  if csv_urls is not None:
    logger.debug(f"CSV Urls: {csv_urls}")
    return csv_urls.split(",")

  logger.error("One of --input-file or --csv-urls must be specified")
  return []

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
