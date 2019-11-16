# -*- encoding: utf-8 -*-


from flask               import render_template, request, url_for, redirect, session
from flask_login         import login_user, logout_user, current_user, login_required
from werkzeug.exceptions import HTTPException, NotFound, abort
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
 
import pyrebase
import random 
import string 

account_sid = 'ACfa7fe832b6a75655a5ec2bcde267f231'
auth_token ='23876e0a1b035d233a438238b3c36490'
incident_type = ''
situation_type = ''

from app        import app, lm, db, bc
from app.models import User
from app.forms  import LoginForm, RegisterForm


config = {
   #ADD API KEY HERE
   "apiKey": "AIzaSyBsQFzuptzHUOx1EAOCCJBasg4uHzXM1eY",
    "authDomain": "test-7d0d1.firebaseapp.com",
    "databaseURL": "https://test-7d0d1.firebaseio.com",
    "projectId": "test-7d0d1",
    "storageBucket": "test-7d0d1.appspot.com",
    "messagingSenderId": "631901717397",
    "appId": "1:631901717397:web:ee17a59f9be32d1602ec9c",
    "measurementId": "G-FR9N37W1GD"
}

SECRET_KEY = 'a secret key'

def generate_id():
    list_id = []
    gen_id = ''.join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for x in range(6)) 
    while gen_id in list_id:
        gen_id = ''.join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for x in range(6)) 
    list_id.append(gen_id)
    return gen_id


def calculate_priority(situation_type, incident_type):
    incident_type = [ 'Poaching',
            'Human Wildlife Conflict',
            'Crop Raiding',
            'Illegal Trade or Trafficking',
            'Animal Death',
            'Damage to livestock, property',
            ]
            
    situation_type = ['critical',
             'significant', 
             'minor'
            ]   
    incident_priority = 5
    if situation_type == 'critical' and incident_type in ['Poaching', 'Human Wildlife Conflict', 'Crop Raiding', 'Illegal Trade or Trafficking']:
                incident_priority = 1
    elif situation_type == 'critical' and incident_type not in ['Poaching', 'Human Wildlife Conflict', 'Crop Raiding', 'Illegal Trade or Trafficking']:
                incident_priority = 2
    elif situation_type == 'significant' and incident_type in ['Poaching', 'Human Wildlife Conflict', 'Crop Raiding', 'Illegal Trade or Trafficking']:
                incident_priority = 2
    elif situation_type == 'significant' and incident_type not in ['Poaching', 'Human Wildlife Conflict', 'Crop Raiding', 'Illegal Trade or Trafficking']:
                incident_priority = 3
    elif situation_type == 'minor' and incident_type in ['Poaching', 'Human Wildlife Conflict', 'Crop Raiding', 'Illegal Trade or Trafficking']:
                incident_priority = 4
    elif situation_type == 'minor' and incident_type not in ['Poaching', 'Human Wildlife Conflict', 'Crop Raiding', 'Illegal Trade or Trafficking']:
                incident_priority = 5        
    else:
                incident_priority = 3    
    
    return incident_priority


firebase = pyrebase.initialize_app(config)

db = firebase.database()


counter=0
@app.route('/sms', methods=['POST'])
def sms():
    global counter
    animal = ''
    incident_type = ''
    situation_type = ''
    incident_location = ''
    
    inc_id = generate_id()
    number = request.form['From']
    message_body = request.form['Body']
    resp = MessagingResponse()
    boolean=False
    if message_body.lower()=='wildsosalert' or  message_body.lower()=='wildsos alert':
        resp.message('Hello {}, please send us the following details in this format:<Animal_Name> <Incident Type Eg. Poaching ,Human Wildlife Conflict etc> <Situation Type Eg.critical ,significant or minor > <Location>'.format(number))
        counter=counter+1
    
    elif counter==0:
        resp.message('Invalid input! Please send WILDSOS if you would like to report any incident.')
        
    else:
        l=message_body.split(' ')
        if len(l)>2:
            animal = l[0]
            incident_type = l[1]
            situation_type = l[2]
            incident_location = l[3] + " " + l[-1]
            counter=0
            resp.message('Thank you! All the details have been recorded by us. We will notify the nearest officer and get back to you as soon as possible')
            incident_priority = calculate_priority(situation_type, incident_type)
            data = { "user_fname": anon,
                     "user_lname": '',
                     "user_phone": number,
                     "user_email": '',
                     "user_address": '',
                     "animal": animal,
                     "incident_id": inc_id,
                     "incident_type": incident_type,
                     "incident_priority": incident_priority,
                     "situation_type": situation_type,
                     "incident_location": incident_location, # Make one for long_lat and one for address
                     "incident_city": '',
                     "incident_country": '',
                     "incident_zipcode": '',
                     "incident_date": '',
                     "incident_time": '',
                     "image_url": '',
                     "incident_description": '',        
                     "assigned_to": "No one",
                     "incident_result": ''    
                    }
            db.child("incident").push(data)
        else:
            resp.message('All details are not entered by the user and try again.')
            counter=0 

    return str(resp)





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
            
            incident_type = request.form['incident_type']
            situation_type = request.form['situation_type']
            incident_priority = calculate_priority(situation_type, incident_type)  

            data = { "user_fname": request.form['fname'],
                     "user_lname": request.form['lname'],
                     "user_phone": request.form['phone'],
                     "user_email": request.form['email'],
                     "user_address": request.form['address'],
                     "animal": request.form['animal'],
                     "incident_id": inc_id,
                     "incident_type": incident_type,
                     "incident_priority": incident_priority,
                     "situation_type": situation_type,
                     "incident_location": request.form['incident_location'], # Make one for long_lat and one for address
                     "incident_city": request.form['incident_city'],
                     "incident_country": request.form['incident_country'],
                     "incident_zipcode": request.form['incident_zipcode'],
                     "incident_date": request.form['incident_date'],
                     "incident_time":request.form['incident_time'],
                     "image_url": request.form['url'],
                     "incident_description": request.form['description'],        
                     "assigned_to": "No one",
                     "incident_result": ''    
            }
            
            db.child("incident").push(data)        
    return render_template('layouts/default.html',
                            content=render_template( 'pages/user.html') )

# Render the table page
@app.route('/table.html')
def all_incidents():
    incident_data = db.child('incident').get()
    incident_data = incident_data.val()
    keys_list = list(incident_data.keys())
    print(keys_list)
    return render_template('layouts/default.html', 
                            content=render_template( 'pages/table.html', incident_data = incident_data, keys_list = keys_list))

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
