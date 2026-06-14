#!/usr/bin/env python3
import sys
import time
import random
import logging
import requests
import concurrent.futures
from faker import Faker

# Force real-time output
sys.stdout.reconfigure(line_buffering=True)

REFERRAL_CODE = "ADD YOUR"
CONCURRENCY = 2
SOLVER_URL = "https://cf-solver-renofc.my.id/api/solvebeta"
SITE_KEY = "0x4AAAAAADfBdk1rel3DLtAS"
QUAXLY_API = "https://panel.quaxly.com/api/user/auth/register"

fake = Faker()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("QuaxlyAutoReg")

# Rotating user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
]

def generate_user():
    first = fake.first_name()
    last = fake.last_name()
    domain = random.choice(["gmail.com","yahoo.com","outlook.com","hotmail.com","protonmail.com","icloud.com","aol.com","mail.com"])
    email = f"{first.lower()}.{last.lower()}{random.randint(100,999)}@{domain}"
    username = f"{first[0].lower()}{last.lower()}{random.randint(100,999)}"
    base = fake.word().capitalize()
    while len(base) < 5:
        base = fake.word().capitalize()
    digits = str(random.randint(10,99)) if random.random()>0.5 else str(random.randint(100,999))
    symbol = random.choice("!@#$%&*")
    password = f"{base}{digits}{symbol}"
    while len(password) < 8:
        password += str(random.randint(0,9))
    return {"first_name":first,"last_name":last,"email":email,"username":username,"password":password}

def get_turnstile_token():
    try:
        resp = requests.post(SOLVER_URL, json={"mode":"turnstile-max","siteKey":SITE_KEY,"url":"https://panel.quaxly.com/auth/register"}, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("token", {}).get("result", {}).get("token")
            if token:
                return token
    except Exception as e:
        logger.warning(f"Token error: {e}")
    return None

def register_one(attempt_id):
    user = generate_user()
    for retry in range(3):
        token = get_turnstile_token()
        if not token:
            logger.warning(f"[{attempt_id}] No token, retry {retry+1}/3")
            time.sleep(5)
            continue
        
        user["turnstile_token"] = token
        user_agent = random.choice(USER_AGENTS)
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json",
            "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8"]),
            "Content-Type": "application/json",
            "Origin": "https://panel.quaxly.com",
            "Referer": "https://panel.quaxly.com/auth/register",
            "Cookie": f"billingreferrals_code={REFERRAL_CODE}"
        }
        try:
            resp = requests.put(QUAXLY_API, json=user, headers=headers, timeout=15)
            
            # Print raw response for debugging
            print(f"[DEBUG] HTTP {resp.status_code} - {resp.text[:300]}")
            
            if resp.status_code in (200, 201):
                data = resp.json()
                # Check multiple possible success fields
                if data.get("success") or data.get("status") == "success" or data.get("message") == "Registration successful":
                    logger.info(f"✅ SUCCESS [{attempt_id}] {user['email']} / {user['password']}")
                    # Save to file
                    with open("successful_accounts.txt", "a") as f:
                        f.write(f"{user['email']}:{user['password']}\n")
                    return True
                else:
                    logger.warning(f"[{attempt_id}] API returned success=False: {data}")
                    return False
            elif resp.status_code == 429:
                logger.warning(f"[{attempt_id}] Rate limited, waiting 30s")
                time.sleep(30)
            else:
                logger.warning(f"[{attempt_id}] HTTP {resp.status_code}: {resp.text[:200]}")
                return False
        except Exception as e:
            logger.warning(f"[{attempt_id}] Request exception: {e}")
            time.sleep(5)
    logger.warning(f"[{attempt_id}] Failed after retries")
    return False

def continuous_register():
    logger.info(f"Start - Concurrency: {CONCURRENCY}, Ref: {REFERRAL_CODE}")
    success = 0
    failed = 0
    counter = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = {executor.submit(register_one, i): i for i in range(1, CONCURRENCY+1)}
        counter = CONCURRENCY
        while True:
            done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                if future.result():
                    success += 1
                else:
                    failed += 1
                del futures[future]
                counter += 1
                futures[executor.submit(register_one, counter)] = counter
                if (success + failed) % 10 == 0:
                    logger.info(f"📊 Stats - Success: {success}, Failed: {failed}, Total: {success+failed}")

if __name__ == "__main__":
    try:
        continuous_register()
    except KeyboardInterrupt:
        logger.info("Stopped")
