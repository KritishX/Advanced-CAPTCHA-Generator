# 🧠 Advanced CAPTCHA Generator

A powerful Flask-based web application that generates **secure, highly customizable CAPTCHAs** with background gradients, geometric noise, wave distortion, shadow effects, and rate-limiting protection.

## 🚀 Features

* 🌀 Gradient background with noise (low, medium, high)
* 🔠 Easy-to-read random characters (excludes confusing ones like `0`, `O`, `I`, `l`)
* 🔏 Rate limiting and session-based CAPTCHA attempts
* 🔁 AJAX-based CAPTCHA refresh without reloading the page
* 💬 Beautiful UI with responsive design (HTML + CSS)
* 🔐 Configurable CAPTCHA length, timeout, and fonts

## 🗂️ Project Structure

```
Advanced-CAPTCHA-Generator/
├── app.py                # Main Flask app with CAPTCHA logic and routes
├── templates/
│   ├── base.html         # Main HTML layout and CAPTCHA form
│   └── result.html       # Result display after verification
├── static/
│   └── fonts/            # Custom fonts for CAPTCHA rendering
```

## ⚙️ Installation

```bash
git clone https://github.com/KritishX/Advanced-CAPTCHA-Generator.git
cd Advanced-CAPTCHA-Generator
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

## 🌐 Usage

* Navigate to `http://localhost:5000`
* Enter the CAPTCHA displayed
* Click **Verify**
* If incorrect, retry up to 3 times or refresh the CAPTCHA

## ⚒️ Configuration

Edit the `Config` class in `app.py` to modify:

```python
CAPTCHA_LENGTH = 6
CAPTCHA_TIMEOUT = 300  # seconds
MAX_ATTEMPTS = 3
IMAGE_WIDTH = 300
IMAGE_HEIGHT = 120
NOISE_LEVEL = 'medium'  # Options: 'low', 'medium', 'high'
```

## 📸 Sample Screenshot

> Include a screenshot of the web UI here if needed

## 📜 License

MIT © [KritishX](https://github.com/KritishX)

