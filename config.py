import os
import json

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SECRET_FILE = os.path.join(BASE_DIR, 'secret.json')
UPLOAD_FOLDER = os.path.join('static')
IMG_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
BASE_URL = "http://127.0.0.1:5000"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in IMG_ALLOWED_EXTENSIONS


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
                                f'{secrets["MYSQL_DATABASE"]}'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
