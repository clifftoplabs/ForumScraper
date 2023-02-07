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

from bs4 import BeautifulSoup
from docopt import docopt
import http.client as http_client
import logging
from typing import AnyStr, List, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
    print(response.headers)
    return get_url_contents(response.headers.get("Location"))

  if response.status != 200:
    logger.error(f"Unexpected status code {response.status} when accessing url {url}")
    return None

  logger.info(f"Retrieved contents of {url}")
  return response.read()

def scrape_forum(url: AnyStr):
  url_contents = get_url_contents(url)
  with open("output.txt", "w+") as fp:
    fp.write(url_contents.decode("utf-8"))
  soup = BeautifulSoup(url_contents, "html.parser")
  posts = soup.find(id="posts")
  print(len(posts.contents))

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
