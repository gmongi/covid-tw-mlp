import configparser
import os

config = configparser.ConfigParser()
config.read('config.ini')
directory = config['DEFAULT']['ScrappedTweeetsDir']
tw_account = config['DEFAULT']['TwitterAccount']
max_results = config['DEFAULT']['MaxResults']
date_since = config['DEFAULT']['DateSince']

os.makedirs(directory, exist_ok=True)
file_name = f"{directory}/{tw_account}-tweets"

flags = {
    '--jsonl': None,
    '--progress': None,
    '--max-results': max_results,
    '--since': date_since,
    'twitter-search': f'"(#Coronavirus) (from:{tw_account}) -filter:replies"',
}

# Build command string
parsed_flags = [f"{key} {value or ''} " for key, value in flags.items()]
command = f"snscrape {''.join(parsed_flags)} > {file_name}.json"
# Call snscrape via OS library
os.system(command)
