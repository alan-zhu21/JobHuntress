from flask import Flask, render_template, redirect, session, flash, request, g
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Job, Category, UserLogin
from forms import RegistrationForm, LoginForm
from sqlalchemy.exc import IntegrityError
from secrets1 import api_key, app_id
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



# Global Variables
g_total_resp = []
g_num_of_jobs = 0
g_category = ''
g_categories = []
g_location = 'anywhere'
g_locations = ['alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado', 'connecticut', 'delaware', 'florida', 'georgia', 'hawaii', 'idaho', 'illinois', 'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana', 'maine', 'maryland', 'massachusetts', 'michigan', 'minnesota', 'mississippi', 'missouri', 'montana', 'nebraska', 'nevada', 'new hampshire', 'new jersey', 'new mexico', 'new york', 'north carolina', 'north dakota', 'ohio', 'oklahoma', 'oregon', 'pennsylvania', 'rhode island', 'south carolina', 'south dakota', 'tennessee', 'texas', 'utah', 'vermont', 'virginia', 'washington', 'west virginia', 'wisconsin', 'wyoming']

API_BASE_URL = "http://api.adzuna.com/v1/api/jobs/us/"
app_key = api_key
app_id_num = app_id
# end global variables



# Main Page
@app.route('/')
def homepage():

    global g_categories
    all_categories = Category.query.all()
    for category in all_categories:
        try: 
            g_categories.append(category.label[:category.label.index('Jobs')-1])
        except ValueError:
            g_categories.append(category.label)

    if not len(g_categories):
        querystring = {
            "content-type": 'application/json',
            "app_id": app_id_num,
            "app_key": app_key,
        }

        res = requests.request("GET", f'{API_BASE_URL}categories', params=querystring)
        for category in res.json()['results'][0]:
            job_category = Category(label=category['label'])
            db.session.add(job_category)
        db.session.commit()
        g_categories = [category.label for category in res.json()['results']]
    
    return render_template('/index.html', categories=g_categories, user=g.user)
# end main page



# User features
@app.before_request
def add_user_to_g():
    '''Add user to global g object if logged in'''

    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])
    else:
        g.user = None


@app.route('/register', methods=['GET', 'POST'])
def register():
    '''Register User'''

    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            username = form.username.data
            password = form.password.data
            # phone = form.phone.data
            email = form.email.data
            linkedin_url = form.linkedin_url.data

            user_auth = UserLogin.register(username, password)
            db.session.add(user_auth)
            db.session.commit()

            user_profile = User(username=username, email=email, linkedin_url=linkedin_url)
            db.session.add(user_profile)
            db.session.commit()

            session['user_id'] = user_auth.id
            flash('Successfully registered!', "success")

            return redirect('/')

        except IntegrityError:
            flash("Username already taken", category='danger')
            return render_template('/my-account-register.html', form=form)

    else:
        if 'user_id' in session:
            flash("Currently logged in, please sign out first")
            return redirect('/')
        return render_template('/my-account-register.html', form=form)



@app.route('/login', methods=['GET','POST'])
def login():
    '''Login user'''

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user_auth = UserLogin.authenticate(username, password)

        if user_auth:
            session['user_id'] = user_auth.id
            flash("Successfully logged in!", "success")
            return redirect('/')
        else:
            flash("Invalid username/password", "danger")
            return render_template('/my-account-login.html', form=form)

    return render_template('/my-account-login.html', form=form)



@app.route('/logout')
def logout():
    '''Logs user out'''

    session.pop('user_id')
    flash('You logged out successfully!')

    return redirect('/')
# end user features



# Browse jobs feature
@app.route('/browse-categories')
def browse_by_category():
    '''Show page for job categories'''

    user = User.query.get_or_404(g.user.id)

    global g_categories
    return render_template('browse-categories.html', categories=g_categories, user=user)



@app.route('/browse-locations')
def browse_by_location():
    '''Show page for job locations'''

    global g_locations
    user = User.query.get_or_404(g.user.id)

    return render_template('browse-locations.html', locations=g_locations, user=user)
# end browse jobs feature



# Search jobs feature
@app.route('/jobs')
def mainpage():
    '''Main page'''

    global g_total_resp
    global g_num_of_jobs
    global g_category
    global g_location

    user = User.query.get_or_404(g.user.id)

    if 'user_id' not in session:
        flash('Please sign up or log in', "danger")
        return redirect('/')

    else:
        return render_template('/search-jobs.html',count=g_num_of_jobs, data=g_total_resp, category=g_category, location=g_location, user=user)



@app.route('/profile')
def profile_page():
    '''Profile page for user'''

    user = User.query.get_or_404(g.user.id)
    
    return render_template('profile.html', user=user)



@app.route('/edit-profile', methods=["POST"])
def edit_profile_page():
    '''Edits profile page for user'''

    user = User.query.get_or_404(g.user.id)
    new_email = request.form['email']
    user.email = new_email
    new_linkedin_url = request.form['linkedin_url']
    user.linkedin_url = new_linkedin_url
    db.session.commit()

    flash("Updated Profile Successfully", 'success')
    
    return redirect('/profile')


@app.route('/job-details/<id>', methods=["GET", "POST"])
def handle_job_details(id):
    '''Handle job details'''

    global g_total_resp

    user = User.query.get_or_404(g.user.id)
    saved_jobs = [job.id for job in g.user.savedjobs]

    job_obj = None
    for job_listing in g_total_resp:
        if job_listing['id'] == id:
            data = job_listing
            description = data['description']
            location = data['location']['display_name']
            title = data['title']
            company = data['category']['label']
            url = data['redirect_url']
            id = data['id']
            category = data['category']['label']
            job_obj = Job(user_id=g.user.id,title=title,company=company,category=category,location=location,description=description,url=url, ext_id=id)

    if job_obj == None:
        saved_jobs_db = g.user.savedjobs
        for job_listing in saved_jobs_db:
            if job_listing.ext_id == id:
                job_obj = job_listing

    
    # import pdb; pdb.set_trace();
    
    return render_template('/job-page.html', job=job_obj, saved_jobs=saved_jobs, user=user)

# end search jobs feature



# Job saving feature
@app.route('/saved-jobs')
def show_saved_jobs():
    '''Shows all the saved jobs'''

    user = User.query.get_or_404(g.user.id)

    if g.user:
        saved_jobs = g.user.savedjobs
        
        return render_template('saved-jobs.html', saved_jobs=saved_jobs, user=user)
    else:
        flash("Please login first.", 'danger')
        return redirect('/login')



@app.route('/savejob/<id>', methods=["POST"])
def savejob(id):
    global g_total_resp
    for job_listing in g_total_resp:
        if job_listing['id'] == id:
            job_obj = job_listing
    title = job_obj['title']
    company = job_obj['company']['display_name']
    location = job_obj['location']['display_name']
    category = job_obj['category']['label']
    description = job_obj['description']
    url = job_obj['redirect_url']
    job_id = job_obj['id']
    new_saved_job = Job(user_id=g.user.id,title=title,company=company,category=category,location=location,description=description,url=url, ext_id=job_id)
    db.session.add(new_saved_job)
    db.session.commit()
    flash('Job Bookmarked!', 'success')
    return redirect("/saved-jobs")



@app.route('/unsavejob/<id>', methods=["POST"])
def unsavejob(id):
    # global g_total_resp
    # for job_listing in g.user.savedjobs:
    #     if job_listing['id'] == id:
    #         job_obj = job_listing
    # title = job_obj['title']
    # company = job_obj['company']['display_name']
    # location = job_obj['location']
    # description = job_obj['description']
    # # url = job_obj['redirect_url']
    # # job_id=job_obj['id']
    # remove_job = Job.query.filter_by(title=title, company=company, location=location, description=description).first()
    unsave_job = Job.query.get_or_404(id)
    db.session.delete(unsave_job)
    db.session.commit()
    flash('Job Removed', 'success')
    return redirect("/saved-jobs")
# end job saving feature



# API call
@app.route('/apicall', methods=["GET", "POST"])
def callapi():
    '''Calls API'''

    global g_total_resp
    global g_num_of_jobs
    global g_category
    global g_location

    if request.method == "POST":
        search_terms = request.form.get('search-terms')
        search_location = request.form.get('search-location')
    else:
        search_terms = request.args.get('search-terms')
        search_location = request.args.get('search-location')

    querystring = {
        "what": search_terms, 
        "results_per_page": 100,
        "content-type": 'application/json',
        "app_id": app_id_num,
        "app_key": app_key,
        "where": search_location
    }

    res = requests.request("GET", f'{API_BASE_URL}search/1', params = querystring)

    if request.method == "POST":
        # data = res.json()['results']
        # description = data['description']
        # location = data['location']['display_name']
        # title = data['title']
        # company = data['category']['label']
        # url = data['redirect_url']
        # id = data['id']
        # category = data['category']['label']
        g_total_resp = res.json()['results']
        g_num_of_jobs = res.json()['count']
        g_category = res.json()['results'][0]['category']['label'] if search_terms else 'Any Category'
        g_location = res.json()['results'][0]['location']['display_name'] if search_location else 'Anywhere'
    else:
        g_total_resp = res.json()['results']
        g_num_of_jobs = res.json()['count']
        g_category = search_terms if search_terms else 'Any Category'
        g_location = search_location if search_location else 'Anywhere'


    return redirect('/jobs')
# end API call

# contact form
@app.route('/contact')
def show_contact_form():
    '''Calls contact form'''

    user = User.query.get_or_404(g.user.id)

    return render_template('contact.html', user=user)
# end contact form