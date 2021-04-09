'''
utils.py
'''
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
from snscrape.modules.twitter import TwitterSearchScraper


def get_tweets(tw_account: str, max_results: int, date_since: str, to_dict: bool = False) -> list:
    """
    Gets and returns a list of tweets
    """
    twitter_query = f'(#Coronavirus) (from:{tw_account}) (since:{date_since}) -filter:replies'
    tweets = []
    for i, tweet in enumerate(TwitterSearchScraper(twitter_query).get_items()):
        tweets.append(tweet if not to_dict else json.loads(tweet.json()))
        if i > max_results:
            break
    return sorted(tweets, key=lambda tweet: tweet.date if not to_dict else tweet['date'])


def save_tweets(filename: str, tweets: list):
    """
    Saves a list of tweets
    """
    if not tweets:
        return
    if not isinstance(tweets[0], dict):
        tweets = [json.loads(tweet.json()) for tweet in tweets]
    with open(filename, 'w') as output_file:
        json.dump(tweets, output_file)


def get_image_path(path: str, filename: str) -> str:
    """
    Get the path of a tweet's image
    """
    return os.path.join(path, filename)


def get_and_save_tweet_image(tweet, img_path: str) -> object:
    """
    Gets and saves a tweet image
    """
    date = tweet.date if not isinstance(tweet, dict) else tweet['date']
    if os.path.isfile(get_image_path(img_path, f'{date}.jpg')):
        return cv2.imread(get_image_path(img_path, f'{date}.jpg'))
    img_url = tweet.media[0].fullUrl if not isinstance(tweet, dict) else tweet['media'][0]['fullUrl']
    req = requests.get(img_url, allow_redirects=True)
    img_bytes = io.BytesIO(req.content)
    with Image.open(img_bytes) as img:
        img.save(get_image_path(img_path, f'{date}.jpg'))
        img = cv2.imread(get_image_path(img_path, f'{date}.jpg'))
        img = cv2.resize(img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((2, 2), np.uint8)
        img = cv2.dilate(img, kernel, iterations=1)
        img = cv2.erode(img, kernel, iterations=1)
        img = cv2.threshold(
            cv2.bilateralFilter(img, 5, 75, 75), 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )[1]
        cv2.imwrite(get_image_path(img_path, f'{date}.jpg'), img)
    return img


def get_and_save_tweets_images(tweets, img_path: str) -> object:
    """
    Gets and saves tweets images
    """
    for tweet in tweets:
        get_and_save_tweet_image(tweet, img_path)


def parse_tweet_image(tweet, img_path: str, img_sizes: dict, img_margins: dict, errors: dict) -> dict:
    """
    Parses a tweets images
    """
    date = tweet.date if not isinstance(tweet, dict) else tweet['date']
    img = cv2.imread(get_image_path(img_path, f'{date}.jpg'))
    if img is None:
        raise Exception(f'Image: {get_image_path(img_path, f"{date}.jpg")} does not exists')
    img = cv2.bitwise_not(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    img_cropped = None
    for contour in cv2.findContours(
        cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)[1], cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
    )[0]:
        approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
        if len(approx) == 4:
            pos_x, pos_y, width, height = cv2.boundingRect(approx)
            if (not(0.95 <= float(width)/height <= 1.05) and
                    img_sizes['width'][1] < width < img_sizes['width'][0] and
                    img_sizes['height'][1] < height < img_sizes['height'][0]):
                img_cropped = img[
                    pos_y+img_margins[0]:pos_y+height-img_margins[0],
                    pos_x+img_margins[0]:pos_x+width-img_margins[1],
                ]
                break
    try:
        total_cases = ''.join(re.findall(r'\d+', pytesseract.image_to_string(img_cropped, config='--psm 13')))
    except TypeError:
        total_cases = errors['IMG_ERROR']
    except ValueError:
        total_cases = errors['OCR_ERROR']
    return {'date': date, 'total_cases': total_cases}


def parse_and_get_tweets_images(tweets, img_path: str, img_sizes: dict, img_margins: dict, errors: dict) -> list:
    """
    Parses and gets tweets images
    """
    result = []
    for tweet in tweets:
        result.append(parse_tweet_image(tweet, img_path, img_sizes, img_margins, errors))
    return sorted(result, key=lambda res: res['date'])


def save_results(results: list, filename: str):
    """
    Save results
    """
    with open(filename, 'w', newline='') as csv_file:
        keys = results[0].keys()
        csv_writer = csv.DictWriter(csv_file, fieldnames=keys)
        csv_writer.writeheader()
        csv_writer.writerows(results)


# Deprecated
def get_tweets_file(filename: str) -> list:
    """
    Read the json file of tweets
    """
    tweets = []
    with open(filename) as file:
        for line in file:
            tweets.append(json.loads(line))
    return tweets
