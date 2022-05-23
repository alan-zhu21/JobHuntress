from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()

bcrypt = Bcrypt()

def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)


class User(db.Model):
    """Class for user-related functions and to reference the users table"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    # password = db.Column(db.Text, nullable=False)
    # phone = db.Column(db.Text, nullable=True)
    email = db.Column(db.Text, nullable=True)
    linkedin_url = db.Column(db.Text, nullable=True)



class UserLogin(db.Model):
    """Class for user login and register"""

    __tablename__ = 'user_auth'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)

    @classmethod
    def register(cls, username, pwd):
        """Register user with hashed password & return user."""

        hashed = bcrypt.generate_password_hash(pwd)
        hashed_utf8 = hashed.decode("utf8")

        return cls(username=username, password=hashed_utf8)

    @classmethod
    def authenticate(cls, username, pwd):
        """Validate that user exists & password is correct."""

        u = UserLogin.query.filter_by(username=username).first()

        if u and bcrypt.check_password_hash(u.password, pwd):
            return u
        else:
            return False



class Job(db.Model):
    """class for referencing the saved_jobs table"""

    __tablename__ = 'saved_jobs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.Text, nullable=False)
    company = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text, nullable=False)
    location = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    ext_id = db.Column(db.Text, nullable=False)

    users = db.relationship('User', backref='savedjobs')



class Category(db.Model):
    '''table for job categories'''

    __tablename__ = 'job_categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.Text, nullable=False)