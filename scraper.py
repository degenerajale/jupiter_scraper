import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time
import sqlite3

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def init_db():
    conn = sqlite3.connect("seen_proposals.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            status TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def is_seen(cursor, title):
    cursor.execute("SELECT 1 FROM proposals WHERE title = ?", (title,))
    return cursor.fetchone() is not None


def mark_seen(cursor, title, status):
    cursor.execute("INSERT OR IGNORE INTO proposals (title, status) VALUES (?, ?)", (title, status))


def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    if response.ok:
        return True
    else:
        print("❌ Telegram send failed:", response.text)
        return False


def fetch_and_send_proposals():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    conn = init_db()
    cursor = conn.cursor()

    try:
        driver.get("https://vote.jup.ag/")
        time.sleep(6)  # wait for JS to render proposals

        rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'cursor-pointer')]")
        print(f"Found {len(rows)} proposal rows.\n")

        for row in rows:
            try:
                title_elem = row.find_element(By.XPATH, "./td[1]/p[1]")
                status_elem = row.find_element(By.XPATH, "./td[3]//div[contains(@class, 'rounded-full')]")
                start_date = row.find_element(By.XPATH, "./td[5]").text.strip().replace("\n", " ")
                end_date = row.find_element(By.XPATH, "./td[6]").text.strip().replace("\n", " ")

                title = title_elem.text.strip()
                status = status_elem.text.strip()

                if is_seen(cursor, title):
                    continue  # already sent

                message = (
                    f"<b>{title}</b>\n"
                    f"Status: <i>{status}</i>\n"
                    f"🟢 Starts: {start_date}\n"
                    f"🔴 Ends: {end_date}"
                )

                print(f"📤 Sending: {title}")
                sent = send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)

                if sent:
                    mark_seen(cursor, title, status)
                    conn.commit()

            except Exception as e:
                print(f"⚠️ Error processing row: {e}")


    finally:
        driver.quit()
        conn.close()


if __name__ == "__main__":
    fetch_and_send_proposals()
