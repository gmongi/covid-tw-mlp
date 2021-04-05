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

ERROR = "error"

# Config setup
config = configparser.ConfigParser()
config.read('config.ini')
TW_DIR = config['DEFAULT']['ScrappedTweeetsDir']
TW_ACCOUNT = config['DEFAULT']['TwitterAccount']
IMG_DIR = config['DEFAULT']['ImageDownloadDir']
MAX_RESULTS = config['DEFAULT']['MaxResults']
LAST_DAY_PATH = 'lastScrapped.tmp'
if os.path.exists(LAST_DAY_PATH):
    with open(LAST_DAY_PATH, 'r') as f:
        date_since = f.read()
else:
    date_since = config['DEFAULT']['DateSince']

def get_image_path(filename):
    return f"{IMG_DIR}/{filename}"

# Images directory
os.makedirs(IMG_DIR, exist_ok=True)

# Tweets directory and json file
os.makedirs(TW_DIR, exist_ok=True)
tw_file_name = f"{TW_DIR}/{TW_ACCOUNT}-tweets.json"

# Command flags
flags = {
    '--jsonl': None,
    '--progress': None,
    '--max-results': MAX_RESULTS,
    '--since': date_since,
    'twitter-search': f'"(#Coronavirus) (from:{TW_ACCOUNT}) -filter:replies"',
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
# Download images to IMG_DIR
for tweet in json_tweets:
    date = tweet["date"][0:10]
    if not os.path.isfile(get_image_path(f"{date}.jpg")):
        img_url = tweet['media'][0]['fullUrl']
        req = requests.get(img_url, allow_redirects=True)
        img_bytes = io.BytesIO(req.content)
        with Image.open(img_bytes) as img:
            # Swap colors
            clr_thld = 100
            red = 223
            green = 10
            blue = 128

            img.save(get_image_path(f"{date}.jpg"))
            img = cv2.imread(get_image_path(f"{date}.jpg"))
            img = cv2.resize(img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            kernel = np.ones((2, 2), np.uint8)
            img = cv2.dilate(img, kernel, iterations=1)
            img = cv2.erode(img, kernel, iterations=1)
            img = cv2.threshold(cv2.bilateralFilter(img, 5, 75, 75), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            # Save
            cv2.imwrite(get_image_path(f"{date}.jpg"), img)

# OCR all collected images
with open('accumulatedTotalCases.csv', 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Date', 'CasesToDate'])
    pattern = re.compile(r'.*(\d+\.*\d*)')
    for img_file in os.listdir(IMG_DIR):
        img = cv2.imread(get_image_path(f"{img_file}"))
        if img is None:
            raise Exception(f"Image: {get_image_path(img_file)} does not exists")                
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.bitwise_not(img)

        _, thrash = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thrash, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        img_cropped = None
        for contour in contours:            
            approx = cv2.approxPolyDP(contour, 0.01* cv2.arcLength(contour, True), True)
            cv2.drawContours(img, [approx], 0, (0, 0, 0), 5)
            x = approx.ravel()[0]
            y = approx.ravel()[1] - 5
            if len(approx) == 4:
                x ,y, w, h = cv2.boundingRect(approx)
                aspectRatio = float(w)/h
                if not(aspectRatio >= 0.95 and aspectRatio <= 1.05) and w < 290 and w > 140 and h > 50 and h < 180:
                    img_cropped = img[y:y+h, x:x+w]
                    break
        try:
            ocr_str = pytesseract.image_to_string(img_cropped, config='--psm 7')
            total_cases = int(ocr_str.strip().replace(".", "").replace("*", "")) if ocr_str else ERROR
        except Exception:
            total_cases = ERROR
        csv_writer.writerow([img_file[0:10], total_cases])
