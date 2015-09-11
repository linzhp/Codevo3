__author__ = 'lzp'
import sys
from os import path
import csv

if __name__ == '__main__':
    with open(sys.argv[1]) as log_file, \
            open(path.join(path.dirname(sys.argv[1]), 'team.csv'), 'w', newline='') as team_file:
        writer = csv.DictWriter(team_file, ['time', 'developers'])
        writer.writeheader()
        writer.writerow({'time':0, 'developers': 1})
        current_record = {}
        prefix1 = 'INFO:root:Developer joined, team size:'
        prefix2 = ''
        for line in log_file:
            if line.startswith(prefix1):
                current_record['developers'] = line[len(prefix1):].strip()
            elif 'developers' in current_record:
                current_record['time'] = line.split(':')[2]
                writer.writerow(current_record)
                current_record = {}
