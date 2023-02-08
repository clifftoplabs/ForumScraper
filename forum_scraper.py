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
logger = logging.getLogger(__name__)

class SoftwareType(Enum):
  CUSTOM = 0
  TABLE_POSTS = 1
  LIST_POSTS = 2

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
  def __init__(self, software: SoftwareType, config: Dict[AnyStr, Any] = dict()):
    self.software = software
    self.config = config
    self.posts: List[ForumPost] = []

  @staticmethod
  def for_software(software: SoftwareType):
    if software == SoftwareType.TABLE_POSTS:
      return TablePostsForumParser(software)
    if software == SoftwareType.LIST_POSTS:
      return ListPostsForumParser(software)

    return CustomForumParser(software, {})

  def parse(self, posts_container: PageElement):
    raise NotImplementedError("Must implement parse method in subclass")

  def clean_string(self, element: PageElement) -> Optional[AnyStr]:
    if element is None:
      return None
    return "".join(element.strings).strip()

  def to_json(self):
    return [post.to_json() for post in self.posts]

# TODO: Dry up these parse functions by using a config to define the search terms
class TablePostsForumParser(ForumParser):
  def parse(self, posts_container: PageElement):
    logger.debug(f"Parsing table posts - Element Count: {len(posts_container.contents)}")

    table_posts = posts_container.find_all("table", id=True)
    for table_post in table_posts:
      self.parse_table_post(table_post)

  def parse_table_post(self, table_post: PageElement):
    post = ForumPost()
    rows = table_post.find_all("tr")
    if len(rows) < 2:
      return

    date_order_cols = rows[0].find_all("td")
    if len(date_order_cols) < 2:
      return

    post.date = self.clean_string(date_order_cols[0])
    post.order = int(self.clean_string(date_order_cols[1]).replace("#", ""))
    post.contents = self.clean_string(rows[1].find(class_="thePostItself"))

    self.posts.append(post)


class ListPostsForumParser(ForumParser):
  def parse(self, posts_container: PageElement):
    logger.debug(f"Parsing list posts - Element Count: {len(posts_container.contents)}")

    list_posts = posts_container.find_all("li", class_="postcontainer")
    for list_post in list_posts:
      self.parse_list_post(list_post)

  def parse_list_post(self, list_post: PageElement):
    post = ForumPost()

    post_header = list_post.find(class_="posthead")
    post.date = self.clean_string(post_header.find(class_="postdate"))
    post.order = int(self.clean_string(post_header.find(class_="nodecontrols")).replace("#", ""))
    post_body = list_post.find(class_="postbody")
    post.title = self.clean_string(post_body.find(class_="title"))
    post.contents = self.clean_string(post_body.find(class_="content"))

    self.posts.append(post)

class CustomForumParser(ForumParser):
  def parse(self, posts_container: PageElement):
    logger.debug(f"Parsing custom software - Element Count: {len(posts_container.contents)} | Config: {self.config}")

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
  posts = soup.find(id="posts")

  software = SoftwareType.CUSTOM
  if posts.name == "ol":
    software = SoftwareType.LIST_POSTS
  if posts.name == "div" and posts.table is not None:
    software = SoftwareType.TABLE_POSTS

  forum_parser = ForumParser.for_software(software)
  forum_parser.parse(posts)

  return json.dumps(forum_parser.to_json(), indent=2)

def scrape_forums(urls: List[AnyStr], is_debug: bool):
  with open(f"output.txt", "w+") as fp:
    for url in urls:
      contents = scrape_forum(url)
      if is_debug:
        fp.write(contents + "\n\n")

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
