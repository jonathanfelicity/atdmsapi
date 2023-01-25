from . import db
from datetime import datetime, timedelta
from app.utils import generate_password_hash, check_password_hash


class User(db.Model):
    # Define columns for the User model
    id = db.Column(db.Integer, primary_key=True)
    avatar = db.Column(db.String(255), default='default.png')
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Create a one-to-many relationship between User and Attendance
    attendances = db.relationship('Attendance', backref='user', lazy=True)

    # Hash the password and check the hashed password
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Attendance(db.Model):
    # Define columns for the Attendance model
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    check_out_time = db.Column(db.DateTime)