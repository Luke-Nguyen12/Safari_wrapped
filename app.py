import os 
import sqlite3
import urllib.parse
import re 
from collections import Counter
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone, timedelta

from flask import Flask, render_template

app = Flask(__name__)

def get_top_google_queries(limit = 10):
    chrome_history_path = Path(os.getenv("LOCALAPPDATA")) / r"Google\Chrome\User Data\Default\History" 

    temp_dir = tempfile.gettempdir()
    temp_db_path = Path(temp_dir) / "History_copy"
    shutil.copy2(chrome_history_path, temp_db_path)

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT url FROM urls")
    urls = [row[0] for row in cursor.fetchall()]
    conn.close()

    pattern = re.compile(r"https://www\.google\.[^/]+/search\?.*?[\?&]q=([^&]+)")

    queries = []  # Will store all matched search terms

    for url in urls:
        match = pattern.search(url)  # Try to match the URL to a Google search
        if match:
            query = urllib.parse.unquote_plus(match.group(1)).lower()
            queries.append(query)  # Add to list of queries

    top = Counter(queries).most_common(limit)
    return [q for q, _ in top], [c for _, c in top]

def chrome_time_from_datetime(dt):
    chrome_epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
    delta = dt.replace(tzinfo=timezone.utc) - chrome_epoch
    return int(delta.total_seconds() * 1_000_000)

def datetime_from_chrome_time(chrome_time):
    chrome_epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
    return chrome_epoch + timedelta(microseconds=chrome_time)

def get_first_and_last_google_queries (limit = 2):

    chrome_history_path = Path(os.getenv("LOCALAPPDATA")) / r"Google\Chrome\User Data\Default\History" 
    temp_dir = tempfile.gettempdir()
    temp_db_path = Path(temp_dir) / "History_copy"
    shutil.copy2(chrome_history_path, temp_db_path)

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    now = datetime.now()
    jan_1 = datetime(now.year, 1, 1)
    start_chrome_time = chrome_time_from_datetime(jan_1)
    end_chrome_time = chrome_time_from_datetime(now)

    cursor.execute(
        "SELECT url, last_visit_time FROM urls WHERE last_visit_time BETWEEN ? AND ? ORDER BY last_visit_time ASC",
        (start_chrome_time, end_chrome_time)
    )

    rows = cursor.fetchall()
    conn.close()

    pattern = re.compile(r"https://www\.google\.[^/]+/search\?.*?[\?&]q=([^&]+)")
    queries = []

    for url, visit_time in rows:
        match = pattern.search(url)
        if match:
            query = urllib.parse.unquote(match.group(1)).lower()
            dt = datetime_from_chrome_time(visit_time).astimezone()
            formatted_time = dt.strftime("%B %d, %Y")
            queries.append((query, formatted_time))

    if not queries:
        return [], []

    first_query, first_time = queries[0]
    last_query, last_time = queries[-1]

   return first_query, first_time, last_query, last_time


@app.route("/")
def index():
   labels, counts = get_top_google_queries()
    first_label, first_time, last_label, last_time = get_first_and_last_google_queries()

    return render_template(
        "index.html",
        labels=labels,
        counts=counts,
        first_query=first_label,
        first_time=first_time,
        last_query=last_label,
        last_time=last_time
    )
if __name__ == "__main__":
    app.run(debug=True)
