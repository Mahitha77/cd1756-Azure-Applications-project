import os
import urllib.parse

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "secret-key")

    # Blob storage
    BLOB_ACCOUNT = os.environ.get("BLOB_ACCOUNT", "ENTER_STORAGE_ACCOUNT_NAME")
    BLOB_STORAGE_KEY = os.environ.get("BLOB_STORAGE_KEY", "ENTER_BLOB_STORAGE_KEY")
    BLOB_CONTAINER = os.environ.get("BLOB_CONTAINER", "ENTER_IMAGES_CONTAINER_NAME")
    BLOB_CONNECTION_STRING = os.environ.get("BLOB_CONNECTION_STRING", None)

    # SQL settings
    SQL_SERVER = os.environ.get("SQL_SERVER", "ENTER_SQL_SERVER_NAME.database.windows.net")
    SQL_DATABASE = os.environ.get("SQL_DATABASE", "ENTER_SQL_DB_NAME")
    SQL_USER_NAME = os.environ.get("SQL_USER_NAME", "ENTER_SQL_SERVER_USERNAME")
    SQL_PASSWORD = os.environ.get("SQL_PASSWORD", "ENTER_SQL_SERVER_PASSWORD")

    # URL-encode username/password in case they contain special chars
    _user = urllib.parse.quote_plus(SQL_USER_NAME)
    _password = urllib.parse.quote_plus(SQL_PASSWORD)

    # SQLAlchemy connection string (pyodbc)
    SQLALCHEMY_DATABASE_URI = (
        f"mssql+pyodbc://{_user}:{_password}@{SQL_SERVER}:1433/{SQL_DATABASE}"
        "?driver=ODBC+Driver+17+for+SQL+Server"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MS Authentication
    # — recommended: set these in the App Service Application settings (ENV vars)
    CLIENT_ID = os.environ.get("CLIENT_ID", "1d33d995-838d-4138-b6fa-89d3ad0c995f")
    CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "wKV8Q~qpZMrP4ML8Rqs9bUoLSdjaqvuO_e3SmatM")

    AUTHORITY = os.environ.get("AUTHORITY", "https://login.microsoftonline.com/common")
    REDIRECT_PATH = os.environ.get("REDIRECT_PATH", "/getAToken")  # must match AAD app registration
    SCOPE = ["User.Read"]

    # Session storage type
    SESSION_TYPE = os.environ.get("SESSION_TYPE", "filesystem")
