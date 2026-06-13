sudo python3 << 'PYEOF'
import os, subprocess

os.makedirs('/opt/quaxly-tester/templates', exist_ok=True)

app_code = '''
import threading, time, random, logging, os
from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
from flask_cors import CORS
from faker import Faker
import concurrent.futures
from functools import wraps
import requests

app = Flask(__name__)
CORS(app)

SECRET_CODE = "SM"
DEFAULT_REF = "SUBHAJIT"
API_URL = "https://panel.quaxly.com/api/user/auth/register"

fake = Faker()

# ---------- Auth ----------
def check_auth():
    return request.cookies.get("auth_code") == SECRET_CODE

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not check_auth():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# ---------- User generation ----------
def generate_user():
    first = fake.first_name()
    last = fake.last_name()
    domain = random.choice(["gmail.com","yahoo.com","outlook.com","hotmail.com","protonmail.com","icloud.com","aol.com","mail.com"])
    email = f"{first.lower()}.{last.lower()}{random.randint(100,999)}@{domain}"
    username = f"{first[0].lower()}{last.lower()}{random.randint(100,999)}"
    base = fake.word().capitalize()
    while len(base) < 5: base = fake.word().capitalize()
    digits = str(random.randint(10,99)) if random.random()>0.5 else str(random.randint(100,999))
    symbol = random.choice("!@#$%&*")
    password = f"{base}{digits}{symbol}"
    while len(password) < 8: password += str(random.randint(0,9))
    return {"first_name":first,"last_name":last,"email":email,"username":username,"password":password}

# ---------- Registration worker (direct API, no CAPTCHA) ----------
def register_one(idx, ref):
    user = generate_user()
    max_retries = 3
    for attempt in range(max_retries):
        # Use a random Tor proxy to rotate IPs (optional, but helps avoid rate limits)
        proxy_port = random.choice(range(9050, 9060))
        proxies = {"http": f"socks5h://127.0.0.1:{proxy_port}", "https": f"socks5h://127.0.0.1:{proxy_port}"}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://panel.quaxly.com",
            "Referer": "https://panel.quaxly.com/auth/register",
            "Cookie": f"billingreferrals_code={ref}"
        }
        try:
            resp = requests.put(API_URL, json=user, headers=headers, proxies=proxies, timeout=15)
            if resp.status_code in (200,201) and resp.json().get("success"):
                return {"username":user["username"],"email":user["email"],"status":"success","message":""}
            elif resp.status_code == 429:
                time.sleep(30)
            else:
                msg = resp.json().get("message", f"HTTP {resp.status_code}")
                return {"username":user["username"],"email":user["email"],"status":"failed","message":msg}
        except Exception as e:
            time.sleep(5)
    return {"username":user["username"],"email":user["email"],"status":"failed","message":"Max retries"}

# ---------- Test runner ----------
test_state = {"running":False,"total":0,"completed":0,"success":0,"failed":0,"results":[]}

def run_load_test(total, concurrency, ref):
    global test_state
    test_state["running"] = True
    test_state["total"] = total
    test_state["completed"] = 0
    test_state["success"] = 0
    test_state["failed"] = 0
    test_state["results"] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(register_one, i, ref) for i in range(1, total+1)]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            test_state["completed"] += 1
            if res["status"] == "success": test_state["success"] += 1
            else: test_state["failed"] += 1
            test_state["results"].append(res)

    test_state["running"] = False

# ---------- Routes ----------
@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('code','').strip() == SECRET_CODE:
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('auth_code', SECRET_CODE, max_age=60*60*24)
            return resp
        error = "Invalid secret code"
    return render_template('login.html', error=error)

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
@login_required
def start():
    global test_state
    if test_state["running"]: return jsonify({"error":"Test already running"}),400
    data = request.json
    total = int(data.get("total",5))
    concurrency = int(data.get("concurrency",1))
    ref_raw = data.get("ref",DEFAULT_REF).strip()
    if ref_raw.startswith("http"):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(ref_raw)
        qs = parse_qs(parsed.query)
        ref = qs.get("ref",[DEFAULT_REF])[0]
    else:
        ref = ref_raw or DEFAULT_REF
    threading.Thread(target=run_load_test, args=(total, concurrency, ref)).start()
    return jsonify({"message":"Test started","total":total,"concurrency":concurrency})

@app.route('/status')
@login_required
def status():
    return jsonify({
        "running": test_state["running"],
        "total": test_state["total"],
        "completed": test_state["completed"],
        "success": test_state["success"],
        "failed": test_state["failed"],
        "results": test_state["results"][-50:]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
'''

with open('/opt/quaxly-tester/app.py', 'w') as f:
    f.write(app_code.strip())

# Keep templates (they are already there)
# Restart service
subprocess.run(['systemctl', 'restart', 'quaxly-tester'], check=True)

print("\n✅ Old fast API panel deployed (no CAPTCHA).")
print("   Open: http://57.158.25.135")
print("   Secret code: SM")
print("   Make sure CAPTCHA is disabled on your Quaxly server!")
PYEOF