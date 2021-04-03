import configparser
import csv
import io
import json
import os
import re
from datetime import date

import pytesseract
import requests
from PIL import Image

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
    img_url = tweet['media'][0]['fullUrl']
    req = requests.get(img_url, allow_redirects=True)
    img_bytes = io.BytesIO(req.content)
    with Image.open(img_bytes) as img:
        # Swap colors
        clr_thld = 100
        red = 223
        green = 10
        blue = 128

        # Pixel-by-pixel will do for now
        width, height = img.size
        for x in range(0, width):
            for y in range(0, height):
                pixel = img.getpixel((x, y))
                if ((pixel[0] in range(red-clr_thld, red+clr_thld))
                   & (pixel[1] in range(green-clr_thld, green+clr_thld))
                   & (pixel[2] in range(blue-clr_thld, blue+clr_thld))):
                    img.putpixel((x, y), (0, 0, 0))

        # Save
        img.save(f'{img_dir}/{tweet["date"][0:10]}.jpg')

# OCR all collected images
with open('accumulatedTotalCases.csv', 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Date', 'CasesToDate'])
    pattern = re.compile(r'.*CONFIRMADOS TOTALES\s*(\d+\.*\d*)')
    for img_file in os.listdir(img_dir):
        img = Image.open(f'{img_dir}/{img_file}')
        ocr_str = pytesseract.image_to_string(img, config='--psm 6')
        search = pattern.search(ocr_str)
        if (search):
            total_cases = search.group(1)
        else:
            total_cases = 'Error'
        csv_writer.writerow([img_file[0:10], total_cases])

# Update last scrapped day
with open(last_day_path, 'w') as f:
    f.write(date.today().strftime('%Y-%m-%d'))
