from flask import Flask
from flask_login import LoginManager
from app.database import init_db
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_key_123")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Initialize database on startup
init_db()

from app import routes, auth_models  # Import routes after app initialization
