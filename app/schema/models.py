from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# initialise the database
db = SQLAlchemy()

# Users table
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), nullable=False, unique=True)
    email = db.Column(db.String(90), nullable=False, unique=True)
    bio = db.Column(db.Text, nullable=True)
    password_hash = db.Column(db.Text, nullable=False)
    profile_picture_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f'Users>>>{self.id}'


# Add more tables as required.