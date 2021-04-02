import configparser
import json
import os
from datetime import date

import requests

# Config setup
config = configparser.ConfigParser()
config.read('config.ini')
tw_dir = config['DEFAULT']['ScrappedTweeetsDir']
tw_account = config['DEFAULT']['TwitterAccount']
img_dir = config['DEFAULT']['ImageDownloadDir']
max_results = config['DEFAULT']['MaxResults']
last_day_path = 'lastScrapped.tmp'
if os.path.exists(last_day_path):
    with open(last_day_path, 'r') as f:
        date_since = f.read()
else:
    date_since = config['DEFAULT']['DateSince']

# Images directory
os.makedirs(img_dir, exist_ok=True)

# Tweets directory and json file
os.makedirs(tw_dir, exist_ok=True)
file_name = f"{tw_dir}/{tw_account}-tweets.json"

# Command flags
flags = {
    '--jsonl': None,
    '--progress': None,
    '--max-results': max_results,
    '--since': date_since,
    'twitter-search': f'"(#Coronavirus) (from:{tw_account}) -filter:replies"',
}

# Build command string
parsed_flags = [f"{key} {value or ''} " for key, value in flags.items()]
command = f"snscrape {''.join(parsed_flags)} > {file_name}"

# Call snscrape via OS library
os.system(command)

# Read the json file we just scraped
json_tweets = []
with open(file_name) as f:
    for line in f:
        tweet = json.loads(line)
        json_tweets.append(tweet)

# Work with the tweets
# Download images to img_dir
for tweet in json_tweets:
    img_url = tweet['media'][0]['previewUrl']
    req = requests.get(img_url, allow_redirects=True)
    with open(f'{img_dir}/{tweet["id"]}.jpg', 'wb') as f:
        f.write(req.content)

# Update last scrapped day
with open(last_day_path, 'w') as f:
    f.write(date.today().strftime('%Y-%m-%d'))
