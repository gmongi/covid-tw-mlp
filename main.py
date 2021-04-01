import configparser
import os

config = configparser.ConfigParser()
config.read('config.ini')
directory = config['DEFAULT']['ScrappedTweeetsDir']
tw_account = config['DEFAULT']['TwitterAccount']

os.makedirs(directory, exist_ok=True)
file_name = f"{directory}/{tw_account}-tweets"
since = "2020-11-01"
until = "2020-11-05"
max_results = 1
flags = {
    '--jsonl': None,
    '--progress': None,
    '--max-results': max_results,
    '--since': since,
    'twitter-search': f'"(#Coronavirus) (from:{tw_account}) -filter:replies '
                      f'until:{until}"',
}

# Build command string
parsed_flags = [f"{key} {value or ''} " for key, value in flags.items()]
command = f"snscrape {''.join(parsed_flags)} > {file_name}.json"
# Call snscrape via OS library
os.system(command)
