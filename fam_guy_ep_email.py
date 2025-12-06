import requests
from datetime import datetime, date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from string import Template
import re
import os
import logging
import argparse

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LATEST_EP_FILE = os.path.join(SCRIPT_DIR, "latest_episode.json")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config", "config.json")
TEMPLATE_FILE = os.path.join(SCRIPT_DIR, "config", "email_template.html")
LOG_FILE = os.path.join(SCRIPT_DIR, "app.log")

def setup_logging(verbose=False):
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO if verbose else logging.ERROR)
    fmt = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%Y-%m-%d %H:%M:%S')

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(fmt)
    log.addHandler(file_handler)

    if verbose:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(fmt)
        log.addHandler(console_handler)

    return log

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def load_template():
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return Template(f.read())

def send_email(subject, body, email_config, log):
    msg = MIMEMultipart()
    msg["From"] = email_config["username"]
    msg["To"] = ", ".join(email_config["to"])
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.sendmail(email_config["username"], email_config["to"], msg.as_string())
    except Exception as e:
        log.error(f"Failed to send email: {e}")
        return False
    return True

def load_previous_episode():
    if os.path.exists(LATEST_EP_FILE):
        with open(LATEST_EP_FILE, "r") as f:
            return json.load(f)
    return None

def save_latest_episode(episode):
    with open(LATEST_EP_FILE, "w") as f:
        json.dump({
            "title": episode["name"],
            "season": episode["season"],
            "episode": episode["number"],
            "airdate": episode["airdate"]
        }, f, indent=2)

def fetch_latest_episode(log):
    url = "https://api.tvmaze.com/singlesearch/shows?q=family+guy&embed=episodes"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        log.error(f"Failed to fetch episode data: {e}")
        return None

    today = date.today().isoformat()
    episodes = data.get("_embedded", {}).get("episodes", [])

    if not episodes:
        log.error("No episodes found in API response")
        return None

    aired = [ep for ep in episodes if ep.get("airdate") and ep["airdate"] <= today]

    if not aired:
        log.error("No aired episodes found")
        return None

    latest = max(aired, key=lambda ep: ep["airdate"])
    summary = latest.get("summary") or "No summary available."
    latest["summary"] = re.sub(r'</?p>', '', summary).strip()
    return latest

def is_new_episode(latest, previous):
    return not previous or previous["season"] != latest["season"] or previous["episode"] != latest["number"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Print output to console')
    args = parser.parse_args()

    log = setup_logging(args.verbose)

    try:
        config = load_config()
        html_template = load_template()
    except Exception as e:
        log.error(f"Failed to load config/template: {e}")
        return

    email_config = config["email"]
    previous_episode = load_previous_episode()
    latest = fetch_latest_episode(log)

    if latest is None:
        return

    if not is_new_episode(latest, previous_episode):
        log.info("No new episode found")
        return

    log.info(f"New episode: S{latest['season']}E{latest['number']} - {latest['name']}")

    subject = f"New Family Guy Episode: S{latest['season']}E{latest['number']}"
    body = html_template.substitute(
        title=latest['name'],
        season=latest['season'],
        episode=latest['number'],
        airdate=latest['airdate'],
        summary=latest['summary']
    )

    if send_email(subject, body, email_config, log):
        save_latest_episode(latest)
        log.info("Email sent successfully")

if __name__ == "__main__":
    main()
