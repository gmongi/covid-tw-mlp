import configparser
import json
import os

# Config setup
config = configparser.ConfigParser()
config.read('config.ini')
directory = config['DEFAULT']['ScrappedTweeetsDir']
tw_account = config['DEFAULT']['TwitterAccount']
max_results = config['DEFAULT']['MaxResults']
date_since = config['DEFAULT']['DateSince']

# Files variables
os.makedirs(directory, exist_ok=True)
file_name = f"{directory}/{tw_account}-tweets.json"

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

for tweet in json_tweets:
    print(tweet['content'])
