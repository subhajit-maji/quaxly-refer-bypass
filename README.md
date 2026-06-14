```markdown
# 🚀 Quaxly Auto Registration Bot

**Continuous, concurrent account registration tool for Quaxly**  
Automates signups using a free Turnstile solver – runs forever in a container or terminal.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- ✅ **Runs 24/7** – never stops, automatically replaces finished workers  
- ⚡ **Concurrent registration** (default 2 parallel, adjustable)  
- 🤖 **Automatic Turnstile solving** – no browser, no manual captcha  
- 👤 **Realistic fake identities** – random names, emails, strong passwords  
- 🕵️ **User‑Agent rotation** – desktop/mobile browsers + language variation  
- 📊 **Live statistics** – success/failure counts every 10 attempts  
- 💾 **Saves accounts** – automatically writes `email:password` to a file  
- 🔄 **Smart retries** – handles token failures and rate limiting (429)  
- 🐳 **Docker ready** – lightweight `slim` image with auto‑restart  

## 📦 Requirements

- Python 3.8+ (or Docker)  
- `requests` and `faker` Python packages  
- Internet connection

## ⚙️ Installation & Setup

### Local

```bash
pip install requests faker
python main.py
```

### Docker

**Dockerfile:**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
RUN pip install requests faker
COPY main.py .
CMD ["python", "-u", "main.py"]
```

**Run:**
```bash
docker build -t quaxly-bot .
docker run -d --name quaxly-bot --restart unless-stopped quaxly-bot
```

## 🔧 Configuration

Edit these variables at the top of `bot.py`:

```python
REFERRAL_CODE = "YOUR_CODE"      # Your Quaxly referral code
CONCURRENCY = 2                  # Parallel registrations
```

## 🚀 Usage

```bash
python main.py
```

All successful accounts are saved to `successful_accounts.txt`.

Press `Ctrl+C` to stop.

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| 0% success rate | Free solver may be down – wait or use paid solver |
| "No token" | Add `time.sleep(10)` inside `get_turnstile_token()` |
| 429 Too Many Requests | Reduce `CONCURRENCY` or add proxies |

## ⚠️ Disclaimer

**For educational purposes only.** Automating registrations may violate Quaxly’s Terms of Service. Use at your own risk.

## 📄 License

MIT License
```
