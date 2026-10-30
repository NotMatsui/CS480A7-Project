import csv
import json
import datetime

with open ('ind_vars.csv', 'r', encoding= 'utf-8') as rawfile:
    with open ('analysis_ready.csv', 'w') as analysisfile:
        derivedvarwriter = csv.writer(analysisfile, delimiter= ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for line in rawfile:

            #PR created to first feedback(in seconds) Time to First Human Response
            pr = json.loads(line)
            created_at = (datetime.datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00")))
            review_delay = None
            comment_delay = None

            if pr["reviews"]:
                first_review = None
                for review in pr["reviews"]:
                    if review["author"] != pr["author"]:
                        first_review = (datetime.datetime.fromisoformat(review["at"].replace("Z", "+00:00")))
                        break
                if first_review is not None:
                    review_delay = (first_review - created_at).total_seconds()

            if pr["comments"]:
                first_comment = None
                for comment in pr["comments"]:
                    if comment["author"] != pr["author"]:
                        first_comment = (datetime.datetime.fromisoformat(comment["at"].replace("Z", "+00:00")))
                        break
                if first_comment is not None:
                    comment_delay = (first_comment - created_at).total_seconds()

            if comment_delay is not None and review_delay is not None:
                if comment_delay > review_delay:    
                    pr["TTFR"] = review_delay
                else:
                    pr["TTFR"] = comment_delay
            elif comment_delay is None:
                pr["TTFR"] = review_delay
            else:
                pr["TTFR"] = comment_delay

            #Commit to feedback delay(in seconds)
            commit_delay = []
            for commit in pr["commits"]:
                commit_time = datetime.datetime.fromisoformat(commit["at"].replace("Z", "+00:00"))
                review_delay_commits = 0
                if pr["reviews"]:
                    for review in pr["reviews"]:
                        if review["author"] != pr["author"]:
                            review_time = datetime.datetime.fromisoformat(review["at"].replace("Z", "+00:00"))
                        else:
                            continue
                        if review_time > commit_time:
                            review_delay_commits = (review_time - commit_time).total_seconds()
                            break
                comment_delay_commits = 0
                if pr["comments"]:
                    for comment in pr["comments"]:
                        if comment["author"] != pr["author"]:
                            comment_time = datetime.datetime.fromisoformat(comment["at"].replace("Z", "+00:00"))                            
                        else:
                            continue
                        if comment_time > commit_time:
                            comment_delay_commits = (comment_time - commit_time).total_seconds()
                            break  
                if comment_delay_commits != 0 and review_delay_commits != 0:
                    if comment_delay_commits > review_delay_commits:
                        commit_delay.append(review_delay_commits)
                    else:
                        commit_delay.append(comment_delay_commits)
                elif comment_delay_commits == 0:
                    commit_delay.append(review_delay_commits)
                else:
                    commit_delay.append(comment_delay_commits)
            pr["commit_delay"] = commit_delay

            #comment to commit delay
            feedback_delay_comments = []
            if pr["comments"]:
                for comment in pr["comments"]:
                    if comment["author"] != pr["author"]:
                        comment_time = datetime.datetime.fromisoformat(comment["at"].replace("Z", "+00:00"))
                        commit_delay_comments = 0
                        for commit in pr["commits"]:
                            commit_time = datetime.datetime.fromisoformat(commit["at"].replace("Z", "+00:00"))
                            if commit_time > comment_time:
                                commit_delay_comments = (commit_time - comment_time).total_seconds()
                                feedback_delay_comments.append(commit_delay_comments)
                                break
                            
                pr["feedback_delay_comments"] = feedback_delay_comments

            #review to commit delay
            feedback_delay_reviews = []
            if pr["reviews"]:
                for review in pr["reviews"]:
                    if review["author"] != pr["author"]:
                        review_time = datetime.datetime.fromisoformat(review["at"].replace("Z", "+00:00"))
                        commit_delay_reviews = 0
                        for commit in pr["commits"]:
                            commit_time = datetime.datetime.fromisoformat(commit["at"].replace("Z", "+00:00"))
                        if commit_time > review_time:
                            commit_delay_reviews = (commit_time - review_time).total_seconds()
                            feedback_delay_reviews.append(commit_delay_reviews)
                            break
                pr["feedback_delay_reviews"] = feedback_delay_reviews
                    
            analysisfile.write(json.dumps(pr) + "\n")

            