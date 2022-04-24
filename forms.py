from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Email

class RegistrationForm(FlaskForm):
    """Form for registration"""

    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])  

class LoginForm(FlaskForm):
    """Form for logging a user in"""

    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])

class APIcall(FlaskForm):
    """Form for the criteria for the API call"""

    search_terms = StringField("Search", validators=[InputRequired()])
    location = StringField("Location", validators=[InputRequired()])
    radius = StringField("Radius", validators=[InputRequired()])
