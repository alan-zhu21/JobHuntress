from flask import Flask, render_template, redirect, session, flash, request
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Skill, SelectedSkill
from forms import RegistrationForm, LoginForm
from sqlalchemy.exc import IntegrityError
from secrets import api_key
import os
import requests

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql:///job_huntress'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'thisisasecret123')
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

connect_db(app)

toolbar = DebugToolbarExtension(app)

g_total_resp = []
g_list_of_jobs = []

@app.route('/')
def homepage():
    return render_template('/templates/home.html')


@app.route('/registration', methods=['GET', 'POST'])
def login():
    '''Register User'''

    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.register(username, password)
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id

        return redirect('/main')

    else:
        return render_template('/templates/registration.html', form=form)


@app.route('/login', methods=['GET','POST'])
def register():
    '''Login user'''

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)

        if user:
            session['user_id'] = user.id
            return redirect('/main')
        else:
            form.username.errors = ["Invalid username/password"]

    return render_template('/templates/login.html', form=form)


@app.route('/logout')
def logout():
    '''Logs user out'''

    session.pop('user_id')

    return redirect('/')


@app.route('/main')
def mainpage():
    '''Main page'''

    if 'user_id' not in session:
        flash('Please sign up or log in')
        return redirect('/')
    
    else:
        return render_template('/templates/main.html',titles=g_list_of_jobs, data=g_total_resp)


API_BASE_URL = "https://job-search4.p.rapidapi.com/"
rapid_api_key = api_key


@app.route('/apicall')
def callapi():
    '''Calls API'''

    search_terms = request.form.get('search-terms')

    querystring = {"query": search_terms, "page":"1"}

    headers = {
	    "X-RapidAPI-Host": "job-search4.p.rapidapi.com",
	    "X-RapidAPI-Key": rapid_api_key
    }

    resp_linkedin = requests.request("GET", f'{API_BASE_URL}/linkedin/search', headers=headers, params=querystring)
    resp_monster = requests.request("GET", f'{API_BASE_URL}/monster/search', headers=headers, params=querystring)

    g_total_resp = resp_linkedin.json()['jobs'] + resp_monster.json()['jobs']
    g_list_of_jobs = [item['title'] for item in g_total_resp]

    return redirect('/main')


# pulls job postings from linkedin and indeed displays it
