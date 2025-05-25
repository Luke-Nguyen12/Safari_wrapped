import os 
import sqlite3
import urllib.parse
import re 
from collections import Counter
from pathlib import Path
import shutil
import tempfile

from flask import Flask, render_template

app = Flask(__name__)

def get_top_google_queries(limit = 10):
    chrome_history_path = Path(os.getenv("LOCALAPPDATA")) / r"Google\Chrome"\User Data\Default\History" 

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
            # Decode the query string (e.g., "openai%20chatgpt" → "openai chatgpt")
            query = urllib.parse.unquote(match.group(1)).lower()
            queries.append(query)  # Add to list of queries

    top = Counter(queries).most_common(limit)
    return [q for q, _ in top], [c for _, c in top]

def index():
    labels, counts = get_top_google_queries()

    return render_template("index.html", labels= labels, counts = counts)

if __name__ = "__main__":
    app.run(debug=True)

