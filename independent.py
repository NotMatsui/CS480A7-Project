import csv
import json
import datetime

with open('cleaned_prs.jsonl', 'r', encoding='utf-8') as file:
    with open('ind_vars.csv', 'w', newline="", encoding='utf-8') as ind_file:
        for line in file:

            pr = json.loads(line)
            pr["code_churn"] = pr["additions"] + pr["deletions"]
            pr["weekday"] = datetime.datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00")).strftime('%A')
            pr["change_scope"] = pr["changed_files"]

            ind_file.write(json.dumps(pr) + "\n")