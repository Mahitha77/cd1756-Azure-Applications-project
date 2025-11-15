import logging
from flask import request, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash

# Example user store (replace with your DB)
# password for admin is "secret" (stored as a hash here)
USER_STORE = {
    "admin": {
        "password_hash": generate_password_hash("secret")  # change to your real hash
    }
}

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    logging.info("Login attempt for username=%s", username)

    # 1) must find user
    user = USER_STORE.get(username)
    if not user:
        logging.warning("Invalid login attempt: username not found: %s", username)
        return "unauthorized", 401

    # 2) check password properly (never compare raw hashes or use wrong operators)
    if not check_password_hash(user['password_hash'], password):
        logging.warning("Invalid login attempt for user: %s", username)
        return "unauthorized", 401

    # 3) success: set session (only now) and return
    session.clear()
    session['user'] = username
    logging.info("admin logged in successfully for user=%s", username)
    return "ok", 200
