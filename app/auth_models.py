from flask_login import UserMixin
from app import login_manager
from app.database import get_db_connection

class User(UserMixin):
    def __init__(self, id, username, role, email):
        self.id = id
        self.username = username
        self.role = role
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, role, email FROM users WHERE id = %s", (user_id,))
    u = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not u:
        return None
    return User(id=u['id'], username=u['username'], role=u['role'], email=u['email'])
