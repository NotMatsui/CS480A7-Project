import json
import os
import sys


import pandas as pd
from rabbit_ng import run_rabbit

IN_PATH = "PRs/Full_data"
DETECTED_BOTS = "detected_bots.txt"
LOG = "rabbit_results.jsonl"  # cache: one line per account RABBIT already answered for
SEED = 42

# note to self:
# comments: general PR conversation~543 authors that dont union with the others
# reviews: review submission
# review comments: inline comments 
FEEDBACK = ["comments", "reviews", "review_comments"]

def load_prs(path: str) -> pd.DataFrame:
    try:
        df = pd.read_json(path, lines=True, dtype=False, convert_dates=False)
    except ValueError:
        sys.exit(f"{path} is not the raw output of main.py (one JSON object per line). "
        "If it was opened in Excel and saved again, use the original file.")
    # Drops missing values within author col
    # I think jsonl cant read "" entries as NaNs but I checked the data doesn't seem to be a problem right now
    df_pr_author = df.dropna(subset=["author"])

    return df_pr_author

def run_rabbit_cached(usernames, token):
    #  read the answers saved by earlier runs into a dictionary
    saved = {}
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            for line in f:
                answer = json.loads(line)
                saved[answer["author"]] = answer

    # find the usernames we haven't asked RABBIT about yet
    not_asked_yet = []
    for username in usernames:
        if username not in saved:
            not_asked_yet.append(username)

    # ask RABBIT about the new ones, saving each answer to the file right away
    for res in run_rabbit(not_asked_yet, api_key=token):
        answer = {"author": res.contributor, "user_type": res.user_type, "confidence": res.confidence}
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(answer, default=str) + "\n")
        saved[answer["author"]] = answer

    #answer for every username asked about
    answers = []
    for username in usernames:
        if username in saved:
            answers.append(saved[username])
    return answers

def find_bots(usernames, token) -> set:
    classified_bots = set()

    for r in run_rabbit_cached(sorted(usernames), token):
        # print("Contributer: ", r["author"], "User Type: ", r["user_type"], "Conf: ", r["confidence"])
        if r["user_type"] == "Bot":
            classified_bots.add(r["author"])
    return classified_bots

def drop_Bot_Authored_PRs(pr_authors, df, token):
    pr_bots = find_bots(pr_authors, token)
    df = df[~df["author"].isin(pr_bots)]
    print(f"{len(pr_bots)} bot PR authors, {len(df)} PRs remain")
    return df, pr_bots

def drop_Bot_Authored_Feedback(pr_authors, df, token):
    feedback_authors = {e["author"] for col in FEEDBACK for events in df[col] for e in events if isinstance(e["author"], str)}
    feedback_bots = find_bots(feedback_authors - pr_authors, token)
    print(f"{len(feedback_bots)} bot feedback authors")
    return feedback_bots

def main() -> None:
    df = load_prs(IN_PATH)
    print(f"{len(df)} PRs, {df['author'].nunique()} unique PR authors")

    token = os.environ.get("GITHUB_TOKEN", "").strip().strip("\"'")

    pr_authors = set(df["author"])

    df, pr_bots = drop_Bot_Authored_PRs(pr_authors, df, token)

    feedback_bots = drop_Bot_Authored_Feedback(pr_authors, df, token)

    with open(DETECTED_BOTS, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(pr_bots | feedback_bots)) + "\n")
    print(f"wrote {len(pr_bots | feedback_bots)} bots to {DETECTED_BOTS}")


if __name__ == "__main__":
    main()
