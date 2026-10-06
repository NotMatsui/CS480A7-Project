import csv
import json
import datetime

with open ('zephyr_prs.csv', 'r', encoding= 'utf-8') as rawfile:
    with open ('analysis_ready.csv', 'w') as analysisfile:
        derivedvarwriter = csv.writer(analysisfile, delimiter= ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for line in rawfile:

            #PR created to first feedback(in seconds) Time to First Human Response
            pr = json.loads(line)
            created_at = (datetime.datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00")))
            if pr["reviews"]:
                first_review = (datetime.datetime.fromisoformat(pr["reviews"][0]["at"].replace("Z", "+00:00")))
                review_delay = (first_review - created_at).total_seconds()
            if pr["comments"]:
                first_comment = (datetime.datetime.fromisoformat(pr["comments"][0]["at"].replace("Z", "+00:00")))
                comment_delay = (first_comment - created_at).total_seconds()
            if comment_delay > review_delay:    
                pr["TTFR"] = review_delay
            else:
                pr["TTFR"] = comment_delay

            #Commit to feedback delay(in seconds)
            commit_delay = []
            for commit in pr["commits"]:
                commit_time = datetime.datetime.fromisoformat(commit["at"].replace("Z", "+00:00"))
                if pr["reviews"]:
                    review_delay_commits = 0
                    for review in pr["reviews"]:
                        review_time = datetime.datetime.fromisoformat(review["at"].replace("Z", "+00:00"))
                        if review_time > commit_time:
                            review_delay_commits = (review_time - commit_time).total_seconds()
                            break
                if pr["comments"]:
                    comment_delay_commits = 0
                    for comment in pr["comments"]:
                        comment_time = datetime.datetime.fromisoformat(comment["at"].replace("Z", "+00:00"))
                        if comment_time > commit_time:
                            comment_delay_commits = (comment_time - commit_time).total_seconds()
                            break
                if comment_delay_commits != 0 and review_delay_commits != 0:
                    if comment_delay_commits > review_delay_commits:
                        commit_delay.append(review_delay_commits)
                    else:
                        commit_delay.append(comment_delay_commits)
            pr["commit_delay"] = commit_delay
            print(pr["commit_delay"])

            #feedback to commit delay

            derivedvarwriter.writerow([pr])

            