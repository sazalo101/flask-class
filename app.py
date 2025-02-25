from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
from pymongo import MongoClient
import secrets
import datetime
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['contact_db']
users_collection = db['users']
contacts_collection = db['contacts']

# Flask-Mail setup
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = ''
mail = Mail(app)

# Database functions
def get_user_by_username(username):
    return users_collection.find_one({'username': username})

def get_user_by_email(email):
    return users_collection.find_one({'email': email})

def add_user(username, email, password):
    user = {
        'username': username,
        'email': email,
        'password': password  # In production, hash the password
    }
    users_collection.insert_one(user)

def add_contact(mobile, email, address, registration_number):
    contact = {
        'mobile': mobile,
        'email': email,
        'address': address,
        'registration_number': registration_number
    }
    contacts_collection.insert_one(contact)

def get_contact_by_registration_number(registration_number):
    return contacts_collection.find_one({'registration_number': registration_number})

def save_reset_token(email, token):
    expiration = datetime.datetime.now() + datetime.timedelta(hours=1)
    users_collection.update_one(
        {'email': email},
        {'$set': {'reset_token': token, 'token_expiry': expiration}}
    )

def get_user_by_reset_token(token):
    return users_collection.find_one({
        'reset_token': token,
        'token_expiry': {'$gt': datetime.datetime.now()}
    })

def update_password(email, new_password):
    users_collection.update_one(
        {'email': email},
        {'$set': {
            'password': new_password,
            'reset_token': None,
            'token_expiry': None
        }}
    )

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if get_user_by_username(username):
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if get_user_by_email(email):
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        add_user(username, email, password)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        
        if user and user['password'] == password:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('contact_form'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/contact_form', methods=['GET', 'POST'])
def contact_form():
    if 'username' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        mobile = request.form['mobile']
        email = request.form['email']
        address = request.form['address']
        registration_number = request.form['registration_number']
        
        add_contact(mobile, email, address, registration_number)
        flash('Contact added successfully!', 'success')
    
    return render_template('contact_form.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'username' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        registration_number = request.form['registration_number']
        contact = get_contact_by_registration_number(registration_number)
        
        if contact:
            return render_template('search_results.html', contact=contact)
        flash('No contact found', 'error')
    
    return render_template('search.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = get_user_by_email(email)
        
        if user:
            # Generate token
            token = secrets.token_urlsafe(32)
            save_reset_token(email, token)
            
            # Send reset email
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request',
                        sender='your-email@gmail.com',
                        recipients=[email])
            msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, please ignore this email.
'''
            mail.send(msg)
            flash('Reset link sent to your email.', 'success')
            return redirect(url_for('login'))
        
        flash('Email address not found.', 'error')
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html')
        
        user = get_user_by_reset_token(token)
        if user and user['email'] == email:
            update_password(email, new_password)
            flash('Password has been reset successfully.', 'success')
            return redirect(url_for('login'))
        
        flash('Invalid or expired reset link.', 'error')
    return render_template('reset_password.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)