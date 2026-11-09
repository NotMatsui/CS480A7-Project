import json
from time import time

def medmean():
    with open ("median_mean_feedback.json", 'w', encoding="utf-8") as provfile:
        with open("analysis_ready.csv", "r", encoding="utf-8") as resultsfile:
            TTFR_delay = []
            fdc_delay = []
            fdr_delay = []
            total_feedback_delay = []
            for line in resultsfile:
                pr = json.loads(line)
                if pr["TTFR"]:
                    TTFR_delay.append(pr["TTFR"])
                    total_feedback_delay.append(pr["TTFR"])
                if pr["feedback_delay_comments"]:
                    fdc_delay.extend(pr.get("feedback_delay_comments", []))
                    total_feedback_delay.extend(pr.get("feedback_delay_comments", []))
                if pr["feedback_delay_reviews"]:
                    fdr_delay.extend(pr.get("feedback_delay_reviews", []))
                    total_feedback_delay.extend(pr.get("feedback_delay_reviews", []))
            TTFR_delay = [x for x in TTFR_delay if x is not None]
            TTFR_delay.sort()
            fdc_delay = [x for x in fdc_delay if x is not None]
            fdc_delay.sort()
            fdr_delay = [x for x in fdr_delay if x is not None]
            fdr_delay.sort()
            total_feedback_delay = [x for x in total_feedback_delay if x is not None]
            total_feedback_delay.sort()
            n = len(TTFR_delay)
            if n == 0:
                TTFR_median = 0
                TTFR_mean = 0
            else:
                TTFR_median = TTFR_delay[n // 2] if n % 2 == 1 else (TTFR_delay[n // 2 - 1] + TTFR_delay[n // 2]) / 2
                TTFR_mean = sum(TTFR_delay) / n
            n = len(fdc_delay)
            if n == 0:
                fdc_median = 0
                fdc_mean = 0
            else:
                fdc_median = fdc_delay[n // 2] if n % 2 == 1 else (fdc_delay[n // 2 - 1] + fdc_delay[n // 2]) / 2
                fdc_mean = sum(fdc_delay) / n
            n = len(fdr_delay)
            if n == 0:
                fdr_median = 0
                fdr_mean = 0
            else:
                fdr_median = fdr_delay[n // 2] if n % 2 == 1 else (fdr_delay[n // 2 - 1] + fdr_delay[n // 2]) / 2
                fdr_mean = sum(fdr_delay) / n
            n = len(total_feedback_delay)
            if n == 0:
                total_feedback_median = 0
                total_feedback_mean = 0
            else:
                total_feedback_median = total_feedback_delay[n // 2] if n % 2 == 1 else (total_feedback_delay[n // 2 - 1] + total_feedback_delay[n // 2]) / 2
                total_feedback_mean = sum(total_feedback_delay) / n
        provenance = {
            "TTFR_median": TTFR_median,
            "TTFR_mean": TTFR_mean,
            "feedback_delay_comments_median": fdc_median,
            "feedback_delay_comments_mean": fdc_mean,
            "feedback_delay_reviews_median": fdr_median,
            "feedback_delay_reviews_mean": fdr_mean,
            "total_feedback_delay_median": total_feedback_median,
            "total_feedback_delay_mean": total_feedback_mean
        }
        json.dump(provenance, provfile, indent=4)
if __name__ == "__main__":
    medmean()