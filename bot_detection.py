import os
import sys


import pandas as pd
from rabbit_ng import run_rabbit

CSV_PATH = "cleaned_prs.jsonl"
DETECTED_BOTS = "detected_bots.txt"
SEED = 42

# note to self:
# comments: general PR conversation~543 authors that dont union with the others
# reviews: review submission
# review comments: inline comments 
FEEDBACK = ["comments", "reviews", "review_comments"]

def load_prs(path: str, year: int) -> pd.DataFrame:
    try:
        df = pd.read_json(path, lines=True, dtype=False, convert_dates=False)
    except ValueError:
        sys.exit(f"{path} is not the raw output of main.py (one JSON object per line). "
        "If it was opened in Excel and saved again, use the original file.")
    # Drops missing values within author col
    # I think jsonl cant read "" entries as NaNs but I checked the data doesn't seem to be a problem at all
    df_pr_author = df.dropna(subset=["author"])

    # return df_pr_author

    # only PRs created in the given year (created_at is an ISO string like "2021-03-04T...")
    return df_pr_author[df_pr_author["created_at"].str[:4] == str(year)]

def find_bots(usernames, token) -> set:
    classified_bots = set()

    for res in run_rabbit(sorted(usernames), api_key=token):
        print("Contributer: ", res.contributor, "User Type: ", res.user_type, "Conf: ", res.confidence)
        if res.user_type == "Bot":
            classified_bots.add(res.contributor)
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

def main(year: int) -> None:
    df = load_prs(CSV_PATH, year)
    print(f"{year}: {len(df)} PRs, {df['author'].nunique()} unique PR authors")

    token = os.environ.get("GITHUB_TOKEN", "").strip().strip("\"'")

    pr_authors = set(df["author"])

    df, pr_bots = drop_Bot_Authored_PRs(pr_authors, df, token)

    feedback_bots = drop_Bot_Authored_Feedback(pr_authors, df, token)

    with open(DETECTED_BOTS, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(pr_bots | feedback_bots)) + "\n")
    print(f"wrote {len(pr_bots | feedback_bots)} bots to {DETECTED_BOTS}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2021)
