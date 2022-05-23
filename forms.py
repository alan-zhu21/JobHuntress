from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField
from wtforms.validators import InputRequired, Email, Length, URL, Optional


class RegistrationForm(FlaskForm):
    """Form for registration"""

    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    # phone = IntegerField("Phone", validators=[Length(min=10, max=10)])
    email = StringField("Email", validators=[Email(message="Must be a valid email address"), Optional()])
    linkedin_url = StringField("Linkedin_url", validators=[URL(), Optional()])


class LoginForm(FlaskForm):
    """Form for logging a user in"""

    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])