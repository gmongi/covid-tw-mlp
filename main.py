import argparse
import csv
import os
import re

import cv2
import pytesseract
from dotenv import load_dotenv

from utils import get_image_path, load_tweets_file, save_tweets_images

load_dotenv()

ERROR = os.getenv('ERROR')
TW_PATH = os.getenv('TW_PATH')
TW_ACCOUNT = os.getenv('TW_ACCOUNT')
IMG_PATH = os.getenv('TW_PATH')
MAX_RESULTS = os.getenv('MAX_RESULTS')
LAST_DAY_FILENAME = os.getenv('LAST_DAY_FILENAME')
try:
    file = open(LAST_DAY_FILENAME, 'r')
    DATE_SINCE = file.read()
except IOError:
    DATE_SINCE = os.getenv('DATE_SINCE')

# Images directory
os.makedirs(IMG_PATH, exist_ok=True)

# Tweets directory and json file
os.makedirs(TW_PATH, exist_ok=True)
TW_FILENAME = f'{TW_PATH}/{TW_ACCOUNT}-tweets.json'


def main():
    # Command flags
    flags = {
        '--jsonl': None,
        '--progress': None,
        '--max-results': MAX_RESULTS,
        '--since': DATE_SINCE,
        'twitter-search': f'"(#Coronavirus) (from:{TW_ACCOUNT}) -filter:replies"',
    }

    # Build command string
    parsed_flags = [f"{key} {value or ''} " for key, value in flags.items()]
    command = f"snscrape {''.join(parsed_flags)} > {TW_FILENAME}"

    # Call snscrape via OS library
    os.system(command)

    json_tweets = load_tweets_file(TW_FILENAME)
    save_tweets_images(IMG_PATH, json_tweets)

    # OCR all collected images
    with open('accumulatedTotalCases.csv', 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Date', 'CasesToDate'])
        pattern = re.compile(r'.*(\d+\.*\d*)')
        for img_file in os.listdir(IMG_PATH):
            img = cv2.imread(get_image_path(IMG_PATH, img_file))
            if img is None:
                raise Exception(f'Image: {get_image_path(IMG_PATH, img_file)} does not exists')                
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
                total_cases = int(ocr_str.strip().replace('.', '').replace('*', '')) if ocr_str else ERROR
            except Exception:
                total_cases = ERROR
            csv_writer.writerow([img_file[0:10], total_cases])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Covid Twitter Municipalidad de La Plata')
    parser.add_argument('--get-tweets', help='get tweets')
    parser.add_argument('--load-images', help='load images')
    parser.add_argument('--process-images', help='process images')
    args = parser.parse_args()
    main()
