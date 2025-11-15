import os
import urllib.parse

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret-key'

    # Blob storage
    BLOB_ACCOUNT = os.environ.get('BLOB_ACCOUNT') or 'ENTER_STORAGE_ACCOUNT_NAME'
    BLOB_STORAGE_KEY = os.environ.get('BLOB_STORAGE_KEY') or 'ENTER_BLOB_STORAGE_KEY'
    BLOB_CONTAINER = os.environ.get('BLOB_CONTAINER') or 'ENTER_IMAGES_CONTAINER_NAME'
    BLOB_CONNECTION_STRING = os.environ.get('BLOB_CONNECTION_STRING')

    # SQL settings
    SQL_SERVER = os.environ.get('SQL_SERVER') or 'ENTER_SQL_SERVER_NAME.database.windows.net'
    SQL_DATABASE = os.environ.get('SQL_DATABASE') or 'ENTER_SQL_DB_NAME'
    SQL_USER_NAME = os.environ.get('SQL_USER_NAME') or 'ENTER_SQL_SERVER_USERNAME'
    SQL_PASSWORD = os.environ.get('SQL_PASSWORD') or 'ENTER_SQL_SERVER_PASSWORD'

    _user = urllib.parse.quote_plus(SQL_USER_NAME)
    _password = urllib.parse.quote_plus(SQL_PASSWORD)

    SQLALCHEMY_DATABASE_URI = (
        f"mssql+pyodbc://{_user}:{_password}@{SQL_SERVER}:1433/{SQL_DATABASE}"
        "?driver=ODBC+Driver+17+for+SQL+Server"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Microsoft Authentication (kept as provided)
    CLIENT_ID = "1d33d995-838d-4138-b6fa-89d3ad0c995f"
    CLIENT_SECRET = "wKV8Q~qpZMrP4ML8Rqs9bUoLSdjaqvuO_e3SmatM"

    AUTHORITY = "https://login.microsoftonline.com/common"
    REDIRECT_PATH = "/getAToken"
    SCOPE = ["User.Read"]

    SESSION_TYPE = "filesystem"
