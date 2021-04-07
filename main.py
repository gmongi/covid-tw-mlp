import argparse
import csv
import os
import re

import cv2
import pytesseract
from dotenv import load_dotenv

from utils import get_image_path, load_tweets_file, save_tweets_images

load_dotenv()

IMG_ERROR = os.getenv('IMG_ERROR')
IMG_PATH = os.getenv('IMG_PATH')
LAST_DAY_FILENAME = os.getenv('LAST_DAY_FILENAME')
MAX_RESULTS = os.getenv('MAX_RESULTS')
OCR_ERROR = os.getenv('OCR_ERROR')
RESULTS_FILE = os.getenv('RESULTS_FILE')
TW_ACCOUNT = os.getenv('TW_ACCOUNT')
TW_PATH = os.getenv('TW_PATH')
try:
    file = open(LAST_DAY_FILENAME, 'r')
    DATE_SINCE = file.read()
except IOError:
    DATE_SINCE = os.getenv('DATE_SINCE')
WIDTH_VALUES = [350, 140]
HEIGHT_VALUES = [180, 50]
MARGIN_RESIZE_VALUES = [6, 6]

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

    results = []
    # OCR all collected images
    for img_file in os.listdir(IMG_PATH):
        date = img_file[0:10]
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
                aspect_ratio = float(w)/h
                if (not(aspect_ratio >= 0.95 and aspect_ratio <= 1.05) and
                    w < WIDTH_VALUES[0] and w > WIDTH_VALUES[1] and
                    h < HEIGHT_VALUES[0] and h > HEIGHT_VALUES[1]):
                    new_y = y+MARGIN_RESIZE_VALUES[0]
                    new_x = x+MARGIN_RESIZE_VALUES[0]
                    new_h = y+h-MARGIN_RESIZE_VALUES[1]
                    new_w = x+w-MARGIN_RESIZE_VALUES[1]
                    img_cropped = img[new_y:new_h, new_x:new_w]
                    break
        try:
            ocr_str = pytesseract.image_to_string(img_cropped, config='--psm 13')
            total_cases = ''.join(re.findall(r'\d+', ocr_str))
        except TypeError:
            total_cases = IMG_ERROR
        except ValueError:
            total_cases = OCR_ERROR
        results.append({'date': date, 'total_cases': total_cases})
    results = sorted(results, key = lambda res: res['date'])

    with open(RESULTS_FILE, 'w', newline='') as csv_file:
        keys = results[0].keys()
        csv_writer = csv.DictWriter(csv_file, fieldnames=keys)
        csv_writer.writeheader()
        csv_writer.writerows(results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Covid Twitter Municipalidad de La Plata')
    parser.add_argument('--get-tweets', help='get tweets')
    parser.add_argument('--load-images', help='load images')
    parser.add_argument('--process-images', help='process images')
    args = parser.parse_args()
    main()
