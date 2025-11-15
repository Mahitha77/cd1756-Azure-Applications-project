import sys
import logging
from flask import Flask, request

# === 1. FORCE all logs to stdout and INFO level ===
for h in logging.root.handlers[:]:
    logging.root.removeHandler(h)

handler = logging.StreamHandler(stream=sys.stdout)
fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
handler.setFormatter(logging.Formatter(fmt=fmt, datefmt="%d-%m-%Y %H:%M:%S"))

root = logging.getLogger()
root.setLevel(logging.INFO)
root.addHandler(handler)

# also ensure werkzeug (Flask dev server) uses the same handler
werk = logging.getLogger('werkzeug')
werk.setLevel(logging.INFO)
werk.handlers[:] = []
werk.addHandler(handler)

# === 2. Create app ===
app = Flask(__name__)

# === 3. Test route to confirm logging works ===
@app.route('/ping')
def ping():
    logging.info("PING route hit")
    print("PING-PRINT")   # direct console test
    return "pong"

# === 4. Example login route: add your real logic here ===
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    # Put your existing auth logic here; this is test logic
    if username.lower() == 'admin' and password == 'secret':
        logging.info("admin logged in successfully")
        print("LOGIN-PRINT: success")
        return "ok", 200
    else:
        logging.warning("Invalid login attempt for username=%s", username)
        print("LOGIN-PRINT: invalid")
        return "unauthorized", 401

if __name__ == "__main__":
    # local debug only
    app.run(host="0.0.0.0", port=8000)
