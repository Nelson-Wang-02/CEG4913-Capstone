from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, login_required, logout_user, current_user, login_manager
from datetime import date
import uuid
from sqlalchemy import or_
from . import db
from .models import User
                            
authenticator = Blueprint('authenticator', __name__)

@authenticator.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        email = request.form.get('email')
        userCust = User.query.filter_by(email=email).first() #get usert object. 
        if userCust: #check if user exists.
            if password == userCust.password:
                flash('Login successful!', category='success')
                login_user(userCust, remember= False) #save current user.
                session['userType'] = 'authenticated'
                return redirect(url_for('home_page.home')) #send user to home page after logging in.
            else:
                flash('Wrong password. Try again.', category= 'error')
        else:
            flash('Unregistered email. Please sign up instead.', category='error')
    return render_template('login.html')

@authenticator.route('/')
def index():
    return redirect(url_for('authenticator.login'))

@authenticator.route("/logout")
@login_required
def logout():
    #logout the current user. 
    session.pop('userType', None)
    logout_user()
    return redirect((url_for('authenticator.login'))) #return over to the login screen when logged out.

def validate_user(email, passwordv1, passwordv2, full_name, address, potential_user, gender) -> bool:
    #catch dupe
    if potential_user:
        return (False, "Account exists with this email, please login instead")
    elif len(passwordv1) < 5:
        return (False, "Password is too short")
    elif passwordv1  != passwordv2:
        return (False, "Passwords do not match")
    elif full_name.strip() == "":
        return (False, "Please enter your name")
    elif(email.strip() == ""):
        return (False, "Please enter your email")
    elif(address.strip() == ""):
        return (False, "Please enter your address")
    elif(gender.strip() == ""):
        return (False, "Please enter your gender")
    return (True, "User input is valid")

@authenticator.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        passwordv1 = request.form.get('passwordTemp')
        passwordv2 = request.form.get('password')
        full_name = request.form.get('fullName')
        user_dob = request.form.get('dob')
        user_id= str(uuid.uuid4())
        user_dor = str(date.today())
        address = request.form.get('address')
        user_weight = request.form.get('weight')
        user_height = request.form.get('height')
        user_gender = request.form.get('gender')
        potential_user = User.query.filter(or_(User.email == email, User.id == user_id)).first()
        validate_result = validate_user(email, 
                                        passwordv1,
                                        passwordv2,
                                        full_name,
                                        address,
                                        potential_user, 
                                        user_gender
                                        )
        if validate_result[0]:
            current_user = User(
                    email= email, 
                    id= user_id, 
                    DOR = user_dor,
                    full_name= full_name, 
                    date_of_birth= user_dob, 
                    goal_weight= 0.0, 
                    goal_str = "", 
                    address = address,
                    current_weight = user_weight, 
                    current_height = user_height, 
                    password= passwordv1, 
                    gender= user_gender, 
                )
            try:
                db.session.add(current_user)
                db.session.commit()
                flash(f"Account created! DOR: {user_dor}", category='success')
            except Exception:
                flash("Account creation failed, please try again.", category='error')
            
            #login the user
            try:
                login_user(current_user, remember= False)
                flash(f"Welcome {full_name}!")
                return redirect(url_for('home_page.home'))
            except Exception:
                flash("Failed to login user")

        else:
            flash(validate_result[1], category='error') #show user error message.
            

    return render_template('signup.html')