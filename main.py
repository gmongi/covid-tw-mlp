'''
main.py
'''
import argparse
import os

from dotenv import load_dotenv

from utils import (get_and_save_tweets_images, get_tweets,
                   parse_and_get_tweets_images, save_results, save_tweets)

load_dotenv()

IMG_PATH = os.getenv('IMG_PATH')
LAST_DAY_FILENAME = os.getenv('LAST_DAY_FILENAME')
MAX_RESULTS = int(os.getenv('MAX_RESULTS'))
RESULTS_FILE = os.getenv('RESULTS_FILE')
TW_ACCOUNT = os.getenv('TW_ACCOUNT')
TW_PATH = os.getenv('TW_PATH')
try:
    file = open(LAST_DAY_FILENAME, 'r')
    DATE_SINCE = file.read()
except IOError:
    DATE_SINCE = os.getenv('DATE_SINCE')
MARGIN_RESIZE_VALUES = [6, 6]
TW_FILENAME = f'{TW_PATH}/{TW_ACCOUNT}-tweets.json'
IMG_SIZES = {'width': [350, 140], 'height': [180, 50]}
MARGINS_SIZE = [6, 6]
ERRORS = {
    'OCR_ERROR': os.getenv('OCR_ERROR'),
    'IMG_ERROR': os.getenv('IMG_ERROR'),
}


def setup():
    """
    Setup base folders
    """
    os.makedirs(IMG_PATH, exist_ok=True)
    os.makedirs(TW_PATH, exist_ok=True)


def main():
    """
    Main function
    """
    tweets = get_tweets(TW_ACCOUNT, MAX_RESULTS, DATE_SINCE, to_dict=True)
    save_tweets(TW_FILENAME, tweets)
    get_and_save_tweets_images(tweets, IMG_PATH)
    result = parse_and_get_tweets_images(tweets, IMG_PATH, IMG_SIZES, MARGINS_SIZE, ERRORS)
    save_results(result, RESULTS_FILE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Covid Twitter Municipalidad de La Plata')
    parser.add_argument('--get-tweets', help='get tweets')
    parser.add_argument('--load-images', help='load images')
    parser.add_argument('--process-images', help='process images')
    args = parser.parse_args()
    setup()
    main()
