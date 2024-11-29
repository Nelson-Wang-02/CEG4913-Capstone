from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, login_required, logout_user, current_user, login_manager
from . import db
import requests

exercise_landing = Blueprint('exercise_landing', __name__)

@exercise_landing.route("/launch-exercise", methods=['GET', 'POST'])
def exercise_landing_page():
    return render_template('exercise_landing.html')




