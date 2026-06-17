import requests
import concurrent.futures
import time
import json
import random
from faker import Faker

fake = Faker()

API_URL = "https://panel.quaxly.com/api/user/auth/register"
REFERRAL_CODE = "SUBHAJIT"
TOTAL_USERS = 5          # adjust as needed
CONCURRENT_WORKERS = 5   # adjust as needed
MIN_DELAY = 0
MAX_DELAY = 0

# ------------------------------------------------------------
# 20+ real browser User‑Agents (desktop & mobile)
# ------------------------------------------------------------
USER_AGENTS = [
    # Chrome – Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Chrome – macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Firefox – Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    # Firefox – macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Safari – macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    # Edge – Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    # Chrome – Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Android Chrome
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.80 Mobile Safari/537.36",
    # iPhone Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    # iPad Safari
    "Mozilla/5.0 (iPad; CPU OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
]

# ------------------------------------------------------------
# Real email providers (no @test.org)
# ------------------------------------------------------------
EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "protonmail.com", "icloud.com", "aol.com", "mail.com"
]

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
def get_random_user_agent():
    return random.choice(USER_AGENTS)

def generate_user():
    """Create a fully realistic user."""
    first_name = fake.first_name()
    last_name = fake.last_name()
    domain = random.choice(EMAIL_DOMAINS)
    email = f"{first_name.lower()}.{last_name.lower()}{fake.random_number(digits=3)}@{domain}"
    username = f"{first_name[0].lower()}{last_name.lower()}{fake.random_number(digits=3)}"

    # Human‑like password – guaranteed ≥ 8 characters
    base_word = fake.word().capitalize()
    while len(base_word) < 5:          # ensure a decent word length
        base_word = fake.word().capitalize()
    digits = str(fake.random_number(digits=2)) if random.random() > 0.5 else str(fake.random_number(digits=3))
    symbol = random.choice("!@#$%&*")
    password = f"{base_word}{digits}{symbol}"
    while len(password) < 8:           # pad with extra digits if still too short
        password += str(fake.random_digit())

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "username": username,
        "password": password,
    }

def register_user(index):
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    user = generate_user()
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://panel.quaxly.com",
        "Referer": "https://panel.quaxly.com/auth/register",
        "Cookie": f"billingreferrals_code={REFERRAL_CODE}"
    }
    try:
        resp = requests.put(API_URL, json=user, headers=headers, timeout=10)
        if resp.status_code in (200, 201):
            body = resp.json()
            if body.get("success"):
                print(f"[{index}] ✅ {user['username']} ({user['email']})")
            else:
                print(f"[{index}] ❌ Success=false: {user['username']} - {body}")
        else:
            err = resp.json() if resp.headers.get('content-type','').startswith('application/json') else resp.text
            print(f"[{index}] ❌ {resp.status_code}: {user['username']} - {err}")
    except Exception as e:
        print(f"[{index}] ⚠️ Exception: {e}")

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
if __name__ == "__main__":
    print(f"Realistic load test: {TOTAL_USERS} signups, {CONCURRENT_WORKERS} concurrent")
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = [executor.submit(register_user, i) for i in range(1, TOTAL_USERS+1)]
        concurrent.futures.wait(futures)
    print("Done.")