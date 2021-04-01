import os

directory = "tweets"
os.makedirs(directory, exist_ok=True)

flags_placeholder = "[FLAGS]"
file_name = f"{directory}/laplatamlp-tweets"
base_command = f"snscrape {flags_placeholder} > {file_name}.json"
since = "2020-11-01"
until = "2020-11-05"
max_results = 1
flags = {
    '--jsonl': None,
    '--progress': None,
    '--max-results': max_results,
    '--since': since,
    'twitter-search': '"(#Coronavirus) (from:LaPlataMLP) -filter:replies '
                      f'until:{until}"',

}

# Build command string
parsed_flags = [f"{key} {value or ''} " for key, value in flags.items()]
command = base_command.replace(flags_placeholder, "".join(parsed_flags))
# Call snscrape via OS library
os.system(command)
