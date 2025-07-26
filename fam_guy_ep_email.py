import requests
from datetime import date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from string import Template
import re
import os
import subprocess
import sys


LATEST_EP_FILE = "latest_episode.json"

# ───────────────────────────────
# CONFIG LOADING
# ───────────────────────────────
def load_config():
    """Load settings from config.json"""
    with open("config/config.json", "r") as f:
        return json.load(f)

def load_template():
    """Load the HTML email template"""
    with open("config/email_template.html", "r", encoding="utf-8") as f:
        return Template(f.read())

# ───────────────────────────────
# EMAIL
# ───────────────────────────────
def send_email(subject, body, email_config):
    """Send an HTML email using SMTP"""
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
        print("✅ Email sent successfully.")
    except Exception as e:
        print("❌ Failed to send email:", e)

# ───────────────────────────────
# EPISODE HANDLING
# ───────────────────────────────
def load_previous_episode():
    """Read the previously stored episode from file (if any)"""
    if os.path.exists(LATEST_EP_FILE):
        with open(LATEST_EP_FILE, "r") as f:
            return json.load(f)
    return None

def save_latest_episode(episode):
    """Overwrite latest_episode.json with new episode details"""
    with open(LATEST_EP_FILE, "w") as f:
        json.dump({
            "title": episode["name"],
            "season": episode["season"],
            "episode": episode["number"],
            "airdate": episode["airdate"]
        }, f, indent=2)
    print(f"📁 Updated {LATEST_EP_FILE} with S{episode['season']}E{episode['number']}.")

def fetch_latest_episode():
    """Get the most recently aired Family Guy episode from TVMaze"""
    url = "https://api.tvmaze.com/singlesearch/shows?q=family+guy&embed=episodes"
    data = requests.get(url).json()

    today = date.today().isoformat()
    episodes = data["_embedded"]["episodes"]
    aired = [ep for ep in episodes if ep["airdate"] <= today]

    latest = max(aired, key=lambda ep: ep["airdate"])
    latest["summary"] = re.sub(r'</?p>', '', latest["summary"]).strip()
    return latest

def is_new_episode(latest, previous):
    """Return True if the latest episode is new compared to previous"""
    return not previous or previous["season"] != latest["season"] or previous["episode"] != latest["number"]
  

def check_and_install_requirements(requirements_file="requirements.txt"):
    """Check if required packages are installed; install them if missing."""
    try:
        with open(requirements_file, "r") as f:
            packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        print("⚠️ requirements.txt not found — skipping auto-install.")
        return

    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"📦 Installing missing package: {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])


# ───────────────────────────────
# MAIN
# ───────────────────────────────
def main():
    check_and_install_requirements()
    
    config = load_config()
    html_template = load_template()
    email_config = config["email"]

    previous_episode = load_previous_episode()
    latest = fetch_latest_episode()

    if not is_new_episode(latest, previous_episode):
        print("\nℹ️    No new episode found. Exiting.")
        return

    print(f"\n🔥 NEW Episode: S{latest['season']}E{latest['number']}")
    print(f"Title: {latest['name']}")
    print(f"Airdate: {latest['airdate']}")
    print(f"Summary: {latest['summary']}")

    subject = f"🔥 New Family Guy Episode: S{latest['season']}E{latest['number']}"
    body = html_template.substitute(
        title=latest['name'],
        season=latest['season'],
        episode=latest['number'],
        airdate=latest['airdate'],
        summary=latest['summary']
    )

    send_email(subject, body, email_config)
    save_latest_episode(latest)

if __name__ == "__main__":
    main()
