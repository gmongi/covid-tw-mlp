import configparser
import io
import json
import os
from datetime import date

import requests
from PIL import Image

# Constants
LEFT_RATIO = .342
TOP_RATIO = .605
RIGHT_RATIO = .480
BOTTOM_RATIO = .703

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
tw_file_name = f"{tw_dir}/{tw_account}-tweets.json"

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
command = f"snscrape {''.join(parsed_flags)} > {tw_file_name}"

# Call snscrape via OS library
os.system(command)

# Read the json file we just scraped
json_tweets = []
with open(tw_file_name) as f:
    for line in f:
        tweet = json.loads(line)
        json_tweets.append(tweet)

# Work with the tweets
# Download images to img_dir
for tweet in json_tweets:
    img_url = tweet['media'][0]['previewUrl']
    req = requests.get(img_url, allow_redirects=True)
    img_bytes = io.BytesIO(req.content)
    with Image.open(img_bytes) as img:
        # Crop total number of cases
        cropped_img = img.crop((img.width * LEFT_RATIO,
                                img.height * TOP_RATIO,
                                img.width * RIGHT_RATIO,
                                img.height * BOTTOM_RATIO))

        # Swap colors
        clr_thld = 60
        red = 223
        green = 10
        blue = 128

        # Pixel-by-pixel will do for now
        width, height = cropped_img.size
        for x in range(0, width):
            for y in range(0, height):
                pixel = cropped_img.getpixel((x, y))
                if ((pixel[0] in range(red-clr_thld, red+clr_thld))
                   & (pixel[1] in range(green-clr_thld, green+clr_thld))
                   & (pixel[2] in range(blue-clr_thld, blue+clr_thld))):
                    cropped_img.putpixel((x, y), (0, 0, 0))

        # Save
        cropped_img.save(f'{img_dir}/{tweet["date"][0:10]}.jpg')

# Update last scrapped day
with open(last_day_path, 'w') as f:
    f.write(date.today().strftime('%Y-%m-%d'))
