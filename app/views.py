# -*- encoding: utf-8 -*-


from flask               import render_template, request, url_for, redirect
from flask_login         import login_user, logout_user, current_user, login_required
from werkzeug.exceptions import HTTPException, NotFound, abort


import pyrebase
import random 
import string 



from app        import app, lm, db, bc
from app.models import User
from app.forms  import LoginForm, RegisterForm


config = {
    "apiKey": "AIzaSyBsQFzuptzHUOx1EAOCCJBasg4uHzXM1eY",
    "authDomain": "test-7d0d1.firebaseapp.com",
    "databaseURL": "https://test-7d0d1.firebaseio.com",
    "projectId": "test-7d0d1",
    "storageBucket": "test-7d0d1.appspot.com",
    "messagingSenderId": "631901717397",
    "appId": "1:631901717397:web:ee17a59f9be32d1602ec9c",
    "measurementId": "G-FR9N37W1GD"
}


def generate_id():
    list_id = []
    gen_id = ''.join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for x in range(6)) 
    while gen_id in list_id:
        gen_id = ''.join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for x in range(6)) 
    list_id.append(gen_id)
    return gen_id

firebase = pyrebase.initialize_app(config)

db = firebase.database()



# provide login manager with load_user callback
@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# authenticate user
@app.route('/logout.html')
def logout():
    logout_user()
    return redirect(url_for('index'))

# register user
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    
    # declare the Registration Form
    form = RegisterForm(request.form)

    msg = None

    if request.method == 'GET': 

        return render_template('layouts/default.html',
                                content=render_template( 'pages/register.html', form=form, msg=msg ) )

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 
        email    = request.form.get('email'   , '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        # filter User out of database through username
        user_by_email = User.query.filter_by(email=email).first()

        if user or user_by_email:
            msg = 'Error: User exists!'
        
        else:         

            pw_hash = password #bc.generate_password_hash(password)

            user = User(username, email, pw_hash)

            user.save()

            msg = 'User created, please <a href="' + url_for('login') + '">login</a>'     

    else:
        msg = 'Input error'     

    return render_template('layouts/default.html',
                            content=render_template( 'pages/register.html', form=form, msg=msg ) )

# authenticate user
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    
    # Declare the login form
    form = LoginForm(request.form)

    # Flask message injected into the page, in case of any errors
    msg = None

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        if user:
            
            #if bc.check_password_hash(user.password, password):
            if user.password == password:
                login_user(user)
                return redirect(url_for('index'))
            else:
                msg = "Wrong password. Please try again."
        else:
            msg = "Unkkown user"

    return render_template('layouts/default.html',
                            content=render_template( 'pages/login.html', form=form, msg=msg ) )

# Render the user page
@app.route('/user.html', methods = ['GET', 'POST'])
def report_incident():
    if request.method == "POST":
            inc_id = generate_id()
            
            data = { "user_fname": request.form['fname'],
                     "user_lname": request.form['lname'],
                     "user_phone": request.form['phone'],
                     "user_email": request.form['email'],
                     "user_address": request.form['address'],
                     "animal": request.form['animal'],
                     "incident_id": inc_id,
                     "incident_type": request.form['incident_type'],
                     "situation_type": request.form['situation_type'],
                     "incident_location": request.form['incident_location'],
                     "incident_city": request.form['incident_city'],
                     "incident_country": request.form['incident_country'],
                     "incident_zipcode": request.form['incident_zipcode'],
                     "incident_date": request.form['incident_date'],
                     "incident_time":request.form['incident_time'],
                     "image_url": request.form['url'],
                     "incident_description": request.form['description']            
            }
            
            db.child("incident").child(inc_id).push(data)        
    return render_template('layouts/default.html',
                            content=render_template( 'pages/user.html') )

# Render the table page
@app.route('/table.html')
def table():

    return render_template('layouts/default.html',
                            content=render_template( 'pages/table.html') )

# Render the typography page
@app.route('/typography.html')
def typography():

    return render_template('layouts/default.html',
                            content=render_template( 'pages/typography.html') )

# Render the icons page
@app.route('/icons.html')
def icons():

    return render_template('layouts/default.html',
                            content=render_template( 'pages/icons.html') )

# Render the icons page
@app.route('/notifications.html')
def notifications():

    return render_template('layouts/default.html',
                            content=render_template( 'pages/notifications.html') )

# App main route + generic routing
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path>')
def index(path):

    content = None

    try:

        # try to match the pages defined in -> pages/<input file>
        return render_template('layouts/default.html',
                                content=render_template( 'pages/'+path) )
    except:
        
        return 'Oupsss :(', 404
