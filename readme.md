# 📺 Family Guy New Episode Emailer

Automatically fetches the latest aired **Family Guy** episode and emails when a new episode is available.

---

## 🔧 Setup

1. **Clone this repo**

2. **Install requirements (or run the script after configureing, will auto install requirements.txt)**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure `config.json`**
   This file holds your email credentials and show API info.

   ```json
   {
       "email": {
           "smtp_server": "smtp.gmail.com",
           "smtp_port": 587,
           "username": "email@gmail.com",
           "password": "password",
           "to": [
               "email1@hotmail.com",
               "email2@gmail.com"
           ]
       },
       "tv_show": {
           "name": "Family Guy",
           "api_url": "https://api.tvmaze.com/singlesearch/shows?q=family-guy&embed=episodes"
       }
   }
   ```

Modify the script to fit your API if needed

   ### 📌 Notes

   * `smtp_server` & `smtp_port`: Your mail provider’s SMTP details (Gmail example shown).
   * `username` & `password`: Your email login (use an **App Password** for Gmail).
   * `to`: List of one or more recipients who should get the notifications.
   * `tv_show`: Can be changed if you want to use a different show (example used TVMaze API format).

4. **Setup a scheduler**

   * **Windows:** Use Task Scheduler to run `fam_guy_ep_email.py` daily.
   * **Linux:** Use `cron` to run the script once a day.
   * **Cloud:** Run it in the cloud.
