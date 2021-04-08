'''
utils.py
'''
import io
import json
import os
import cv2
import requests
import numpy as np
from PIL import Image


def get_image_path(path: str, filename: str) -> str:
    """
    Get the path of a tweet's image
    """
    return os.path.join(path, filename)


def load_tweets_file(filename: str) -> list:
    """
    Read the json file of tweets
    """
    tweets = []
    with open(filename) as file:
        for line in file:
            tweets.append(json.loads(line))
    return tweets


def save_tweet_image(img_path: str, tweet: dict):
    """
    Get image from a tweet
    """
    date = tweet['date'][0:10]
    if os.path.isfile(get_image_path(img_path, f'{date}.jpg')):
        return
    img_url = tweet['media'][0]['fullUrl']
    req = requests.get(img_url, allow_redirects=True)
    img_bytes = io.BytesIO(req.content)
    with Image.open(img_bytes) as img:
        img.save(get_image_path(img_path, f'{date}.jpg'))
        img = cv2.imread(get_image_path(img_path, f'{date}.jpg'))
        img = cv2.resize(
            img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC,
        )
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((2, 2), np.uint8)
        img = cv2.dilate(img, kernel, iterations=1)
        img = cv2.erode(img, kernel, iterations=1)
        img = cv2.threshold(
            cv2.bilateralFilter(img, 5, 75, 75), 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )[1]
        # Save
        cv2.imwrite(get_image_path(img_path, f'{date}.jpg'), img)


def save_tweets_images(img_path: str, tweets: list):
    """
    Get images from the tweets and save it
    """
    for tweet in tweets:
        save_tweet_image(img_path, tweet)
