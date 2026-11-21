
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = "analysis_ready.csv"
OUTPUT_DIR = "graphs"
ZOOM_DIR = os.path.join(OUTPUT_DIR, "zoom_99")

SECONDS_PER_HOUR = 3600
WEEKDAYS = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ZOOM_DIR, exist_ok=True)

plt.rcParams.update({
    "figure.figsize": (11, 7),
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "savefig.dpi": 300,
    "axes.grid": True,
    "grid.alpha": 0.25
})


def load_data(filename):
    print(f"Loading {filename}...")

    with open(filename, "r", encoding="utf-8") as file:
        first_line = file.readline().strip()

    if first_line.startswith("{"):
        data = pd.read_json(filename, lines=True)
    else:
        data = pd.read_csv(filename, low_memory=False)

    print(f"Loaded {len(data):,} observations.")

    return data


df = load_data(DATA_FILE)

# VALIDATE DATA
required_columns = [
    "code_churn",
    "weekday",
    "change_scope",
    "feedback_delay_comments",
    "feedback_delay_reviews",
    "TTFR",
    "commit_delay"
]

missing = [c for c in required_columns if c not in df.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")

# PROCESS FEEDBACK TIMES

def parse_values(value):
    """Handle numeric values, lists, and JSON-encoded lists."""

    if value is None:
        return []

    if isinstance(value, str):
        value = value.strip()

        if not value or value.lower() in ("nan", "none", "null"):
            return []

        if value.startswith("["):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return []

        else:
            try:
                number = float(value)
                return [number] if np.isfinite(number) else []
            except ValueError:
                return []

    if isinstance(value, (list, tuple, np.ndarray)):
        results = []
        for item in value:
            results.extend(parse_values(item))
        return results

    try:
        number = float(value)
        return [number] if np.isfinite(number) else []
    except (ValueError, TypeError):
        return []


def median_hours(value):
    values = [
        v for v in parse_values(value)
        if v >= 0
    ]

    if not values:
        return np.nan

    return float(np.median(values)) / SECONDS_PER_HOUR


print("Calculating feedback measurements...")

df["comment_to_commit"] = (
    df["feedback_delay_comments"].apply(median_hours)
)

df["review_to_commit"] = (
    df["feedback_delay_reviews"].apply(median_hours)
)

df["ttfr_hours"] = (
    df["TTFR"].apply(median_hours)
)

df["commit_to_feedback"] = (
    df["commit_delay"].apply(median_hours)
)

# PROCESS INDEPENDENT VARIABLES

df["code_churn"] = pd.to_numeric(
    df["code_churn"], errors="coerce"
)

df["files_changed"] = pd.to_numeric(
    df["change_scope"], errors="coerce"
)


def normalize_weekday(value):
    if pd.isna(value):
        return np.nan

    value = str(value).strip()

    if value in WEEKDAYS:
        return value

    try:
        number = int(value)
        if 0 <= number <= 6:
            return WEEKDAYS[number]
    except ValueError:
        pass

    return np.nan


df["weekday"] = df["weekday"].apply(normalize_weekday)

# FEEDBACK METRICS

feedback_metrics = [
    ("comment_to_commit", "Comment to Commit"),
    ("review_to_commit", "Review to Commit"),
    ("ttfr_hours", "Time to First Response (TTFR)"),
    ("commit_to_feedback", "Commit to Next Human Feedback")
]


# HELPER: PREPARE DATA

def prepare_data(x_column, metric):

    data = df[[x_column, metric]].copy()

    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.dropna()

    data = data[
        (data[x_column] >= 0) &
        (data[metric] >= 0)
    ]

    return data

# HELPER: MEDIAN TREND LINE

def add_median_trend(ax, data, x_column, metric):
    """
    Divide the data into approximately 20 quantile bins
    and plot the median of each bin.

    This is less sensitive to extreme observations
    than an ordinary linear regression line.
    """

    if len(data) < 20:
        return

    log_x = np.log1p(data[x_column])

    bins = pd.qcut(
        log_x,
        q=20,
        duplicates="drop"
    )

    trend = (
        data.assign(_bin=bins)
        .groupby("_bin", observed=True)
        .agg({
            x_column: "median",
            metric: "median"
        })
        .dropna()
    )

    if len(trend) >= 2:
        ax.plot(
            trend[x_column],
            trend[metric],
            color="red",
            linewidth=2.5,
            label="Median Trend",
            zorder=3
        )
        ax.legend()

def create_scatter_graph(
    x_column,
    x_label,
    metric,
    metric_label,
    graph_number
):

    data = prepare_data(x_column, metric)

    if data.empty:
        print(f"Skipping Graph {graph_number}: no valid data.")
        return

    fig, ax = plt.subplots()

    ax.scatter(
        data[x_column],
        data[metric],
        alpha=0.18,
        s=9,
        label="Pull requests"
    )

    add_median_trend(ax, data, x_column, metric)

    ax.set_xscale("symlog", linthresh=1)
    ax.set_yscale("symlog", linthresh=1)

    ax.set_xlabel(x_label)
    ax.set_ylabel("Feedback Time (Hours)")

    ax.set_title(
        f"Graph {graph_number}: {x_label} vs {metric_label}"
    )

    ax.text(
        0.02, 0.97,
        f"n = {len(data):,}",
        transform=ax.transAxes,
        verticalalignment="top"
    )

    fig.tight_layout()

    fig.savefig(
        os.path.join(OUTPUT_DIR, f"graph_{graph_number}.png")
    )

    plt.close(fig)

    # 99TH PERCENTILE ZOOM

    x_limit = data[x_column].quantile(0.99)
    y_limit = data[metric].quantile(0.99)

    zoom = data[
        (data[x_column] <= x_limit) &
        (data[metric] <= y_limit)
    ]

    fig, ax = plt.subplots()

    ax.scatter(
        zoom[x_column],
        zoom[metric],
        alpha=0.2,
        s=9,
        label="Pull requests"
    )

    add_median_trend(ax, zoom, x_column, metric)

    ax.set_xlabel(x_label)
    ax.set_ylabel("Feedback Time (Hours)")

    ax.set_title(
        f"Graph {graph_number}: {x_label} vs {metric_label}\n"
        "99th Percentile View"
    )

    ax.text(
        0.02, 0.97,
        f"n = {len(zoom):,} | Full dataset: {len(data):,}",
        transform=ax.transAxes,
        verticalalignment="top"
    )

    fig.tight_layout()

    fig.savefig(
        os.path.join(
            ZOOM_DIR,
            f"graph_{graph_number}_zoom99.png"
        )
    )

    plt.close(fig)

    print(
        f"Graph {graph_number} complete: "
        f"{len(data):,} full observations, "
        f"{len(zoom):,} zoom observations."
    )

for i, (metric, label) in enumerate(feedback_metrics):

    create_scatter_graph(
        "code_churn",
        "Code Churn (Additions + Deletions)",
        metric,
        label,
        i
    )

for i, (metric, label) in enumerate(
    feedback_metrics, start=4
):

    data = df[["weekday", metric]].copy()

    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.dropna()

    data = data[data[metric] >= 0]

    weekday_data = [
        data.loc[data["weekday"] == day, metric].values
        for day in WEEKDAYS
    ]

    counts = [
        len(values) for values in weekday_data
    ]

    labels = [
        f"{day}\n(n={count:,})"
        for day, count in zip(WEEKDAYS, counts)
    ]

    fig, ax = plt.subplots()

    ax.boxplot(
        weekday_data,
        labels=labels,
        showfliers=False
    )
    
    ax.set_yscale("symlog", linthresh=1)

    ax.set_xlabel("Weekday PR Was Created")
    ax.set_ylabel("Feedback Time (Hours)")

    ax.set_title(
        f"Graph {i}: Weekday vs {label}"
    )

    ax.grid(axis="y", alpha=0.3, which="both")

    fig.tight_layout()

    fig.savefig(
        os.path.join(OUTPUT_DIR, f"graph_{i}.png")
    )

    plt.close(fig)

    print(f"Graph {i} complete.")


for i, (metric, label) in enumerate(
    feedback_metrics, start=8
):

    create_scatter_graph(
        "files_changed",
        "Number of Files Changed",
        metric,
        label,
        i
    )
    
print("\nCOMMENT TO COMMIT FEEDBACK TIME CHECK")

print(
    df["comment_to_commit"].describe(
        percentiles=[0.90, 0.95, 0.99, 0.999]
    )
)

print("\nLongest feedback times (hours):")

print(
    df.nlargest(10, "comment_to_commit")[
        ["comment_to_commit", "code_churn", "change_scope"]
    ].to_string(index=False)
)

print("\n========================================")
print("GRAPH GENERATION COMPLETE")
print("========================================")

print(f"Total input observations: {len(df):,}")

for metric, label in feedback_metrics:
    valid = df[metric].notna().sum()
    print(f"{label}: {valid:,} valid observations")

print(f"\nMain graphs: {OUTPUT_DIR}")
print(f"Zoomed graphs: {ZOOM_DIR}")

print("\nGenerated 12 main graphs and up to 8 zoomed graphs.")
