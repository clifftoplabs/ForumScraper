# Forum Scraper
Simple utility to scrape forum data from specified URLs

## Install
Create a virtual environment and install the dependencies
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run
You can run the solution with the following command:
```
python3 forum_scraper.py -f input.txt
```
or
```
python3 forum_scraper.py -u https://www.e90post.com/forums/showthread.php?t=1000,https://forums.hexus.net/showthread.php?t=1234
```

You can can also see a full list of options by looking at the help documentation:
```
python3 forum_scraper.py [-h | --help]
```
