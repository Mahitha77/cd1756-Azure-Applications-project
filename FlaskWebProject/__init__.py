import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session

from config import Config

LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'

app = Flask(__name__)
app.config.from_object('config.Config')

# Stream logs to stdout (Azure Log Stream reads this)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Optional: also write to a rolling file if storage is enabled
handlers = [stream_handler]
if os.environ.get("WEBSITES_ENABLE_APP_SERVICE_STORAGE", "false").lower() == "true":
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=1_000_000, backupCount=3)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handlers.append(file_handler)

for h in handlers:
    app.logger.addHandler(h)
app.logger.setLevel(logging.INFO)

app.logger.info("Flask app initialized and logging configured.")

# Initialize extensions
Session(app)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

# Import views (registers routes)
from FlaskWebProject import views  # noqa: E402,F401
