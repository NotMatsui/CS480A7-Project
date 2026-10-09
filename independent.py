import csv
import json
import datetime

with open('PRs/2023.csv', 'r', encoding='utf-8') as file:
    with open('ind_vars.csv', 'w', newline="", encoding='utf-8') as ind_file:
        ind_writer = csv.writer(ind_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for line in file:

            pr = json.loads(line)
            pr["code_churn"] = pr["additions"] + pr["deletions"]
            pr["weekday"] = datetime.datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00")).strftime('%A')

            ind_writer.writerow([pr])