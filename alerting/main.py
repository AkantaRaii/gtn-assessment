import re
import json

# this is a timestamp pattern that matches 'YYYY-MM-DD HH:MM:SS'
time_stamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')

'''
i decided to use a json file to store the rules,
which allows for easy modification without changing the code.
and this is a fucntion to  load rules from a json file and return a list of compiled regex patterns.
format of json file:
{
    "patterns": [
        "failed login attempt",
        "unauthorized access",
        "malicious activity"
    ]
}
one can add more patterns.
'''
def load_rules():
    with open('rules.json','r') as file:
        rules=json.load(file)
        return [re.compile(pattern, re.IGNORECASE) for pattern in rules['patterns']]
        


''' this is main finction that monitors the log file for any matches with the rules.
it reads the log file line by line, checks each line against the compiled regex patterns,
and prints an alert if a match is found.
it also extracts the timestamp from the log line if available.
'''
def monitor_logs(log_file_path):
    with open(log_file_path,'r') as file:
        for line in file:
            for pattern in load_rules():
                if pattern.search(line):
                    timestamp_obj=time_stamp_pattern.search(line)
                    timestamp=timestamp_obj.group(0) if timestamp_obj else "unknown time"
                    match_text=pattern.search(line).group(0)
                    print(f"ALERT: {match_text} DETECTED AT {timestamp}\n")

log_file_path= 'log.txt'

#call the function to start monitoring the log file
monitor_logs(log_file_path)
