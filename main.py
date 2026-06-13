#!/usr/bin/env python3
import threading
import time
import random
import logging
import requests
import concurrent.futures
from faker import Faker

REFERRAL_CODE = "SUBHAJIT"
CONCURRENCY = 2
SOLVER_URL = "https://cf-solver-renofc.my.id/api/solvebeta"
SITE_KEY = "0x4AAAAAADfBdk1rel3DLtAS"
QUAXLY_API = "https://panel.quaxly.com/api/user/auth/register"

fake = Faker()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QuaxlyAutoReg")

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
            time.sleep(5)
            continue
        user["turnstile_token"] = token
        headers = {"User-Agent":"Mozilla/5.0","Accept":"application/json","Content-Type":"application/json","Origin":"https://panel.quaxly.com","Referer":"https://panel.quaxly.com/auth/register","Cookie":f"billingreferrals_code={REFERRAL_CODE}"}
        try:
            resp = requests.put(QUAXLY_API, json=user, headers=headers, timeout=15)
            if resp.status_code in (200,201) and resp.json().get("success"):
                logger.info(f"✅ SUCCESS [{attempt_id}] {user['email']} / {user['password']}")
                return True
            elif resp.status_code == 429:
                time.sleep(30)
            else:
                logger.warning(f"[{attempt_id}] Fail: {resp.json().get('message','?')}")
                return False
        except Exception as e:
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