import configparser
import csv
import io
import json
import os
import re

import cv2
import numpy as np
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

        # Save
        img.save(f'{img_dir}/{tweet["date"][0:10]}.jpg')

# OCR all collected images
with open('accumulatedTotalCases.csv', 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Date', 'CasesToDate'])
    pattern = re.compile(r'.*CONFIRMADOS TOTALES\s*(\d+\.*\d*)')
    for img_file in os.listdir(img_dir):
        img = cv2.imread(f'{img_dir}/{img_file}')
        img = cv2.resize(img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((2, 2), np.uint8)
        img = cv2.dilate(img, kernel, iterations=1)
        img = cv2.erode(img, kernel, iterations=1)
        img = cv2.threshold(cv2.bilateralFilter(img, 5, 75, 75), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        cv2.imwrite(f'{img_dir}/{img_file}', img)

        ocr_str = pytesseract.image_to_string(img, config='--psm 6')
        search = pattern.search(ocr_str)
        if (search):
            total_cases = search.group(1)
        else:
            total_cases = 'Error'
        csv_writer.writerow([img_file[0:10], total_cases])
