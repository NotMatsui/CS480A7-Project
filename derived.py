import csv

with open ('zephyr_prs.csv', 'w', newline = '', encodint='utf-8') as csvfile:
    data = csv.reader(csvfile)
    for row in data:
        