from flask import Flask, render_template, redirect, session, flash, request
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, SavedJob
from forms import RegistrationForm, LoginForm
from sqlalchemy.exc import IntegrityError
from secrets1 import api_key
import os
import requests

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql:///job_huntress'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'thisisasecret123')
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

connect_db(app)

with app.app_context():
    db.create_all()

toolbar = DebugToolbarExtension(app)

g_total_resp = []
g_list_of_jobs = []


@app.route('/')
def homepage():
    return render_template('/home.html')


@app.route('/registration', methods=['GET', 'POST'])
def login():
    '''Register User'''

    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            username = form.username.data
            password = form.password.data

            user = User.register(username, password)
            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id
            flash('Successfully registered!', "success")

            return redirect('/main')

        except IntegrityError:
            flash("Username already taken", category='danger')
            return render_template('registration.html', form=form)

    else:
        return render_template('/registration.html', form=form)


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
            flash("Successfully logged in!", "success")
            return redirect('/main')
        else:
            flash("Invalid username/password", "danger")
            return render_template('/login.html', form=form)

    return render_template('/login.html', form=form)


@app.route('/logout')
def logout():
    '''Logs user out'''

    session.pop('user_id')
    flash('You logged out successfully!')

    return redirect('/')


@app.route('/main')
def mainpage():
    '''Main page'''

    global g_list_of_jobs
    global g_total_resp

    if 'user_id' not in session:
        flash('Please sign up or log in', "danger")
        return redirect('/')

    else:
        return render_template('/main.html',titles=g_list_of_jobs, data=g_total_resp)

@app.route('/<int:user_id>')
def profilepage(user_id):
    if session['user_id']:
        user = User.query.get_or_404(user_id)
        saved_jobs = user.savedjobs

        return render_template('/profile.html', saved_jobs=saved_jobs, user=user)
    else:
        flash("Please login first.", 'danger')
        return redirect('/')


@app.route('/savejob')
def savejob():
    title = request.args.get('title')
    company_name = request.args.get('company_name')
    location = request.args.get('location')
    description = request.args.get('description')
    url = request.args.get('url')
    new_saved_job = SavedJob(user_id=session['user_id'],title=title,company_name=company_name,location=location,description=description,url=url)
    db.session.add(new_saved_job)
    db.session.commit()
    flash('Job Saved!', 'success')
    return redirect("/<session['user_id']>")


API_BASE_URL = "https://job-search4.p.rapidapi.com/"
rapid_api_key = api_key


@app.route('/apicall', methods=["POST"])
def callapi():
    '''Calls API'''

    search_terms = request.form.get('search-terms')

    querystring = {"query": search_terms, "page":"1"}

    headers = {
	    "X-RapidAPI-Host": "job-search4.p.rapidapi.com",
	    "X-RapidAPI-Key": rapid_api_key
    }

    resp_linkedin = requests.request("GET", f'{API_BASE_URL}/linkedin/search', headers=headers, params=querystring)
    # resp_monster = requests.request("GET", f'{API_BASE_URL}/monster/search', headers=headers, params=querystring)

    global g_total_resp
    g_total_resp = resp_linkedin.json()['jobs'] 
    # + resp_monster.json()['jobs']
    global g_list_of_jobs
    g_list_of_jobs = [item['title'] for item in g_total_resp]

    return redirect('/main')


# pulls job postings from linkedin and indeed displays it
