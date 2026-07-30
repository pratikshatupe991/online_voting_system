import os
import json

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SECRET_FILE = os.path.join(BASE_DIR, 'secret.json')


def load_secrets():
    """Loads secrets from the JSON file if it exists."""
    if os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, 'r') as file:
            return json.load(file)
    return {}


secrets = load_secrets()


class Config:
    SECRET_KEY = secrets.get('SECRET_KEY') or os.environ.get('SECRET_KEY') or 'super-secret-key-change-this'
    SQLALCHEMY_DATABASE_URI = (secrets.get('DATABASE_URL') or os.environ.get('DATABASE_URL') or
                               (f'mysql+pymysql://{secrets["MYSQL_USERNAME"]}:{secrets["MYSQL_PASSWORD"]}@localhost/'
                                f'voting_db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
