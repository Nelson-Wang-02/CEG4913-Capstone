from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, login_required, logout_user, current_user, login_manager
from . import db
from .models import User, Exercises
from datetime import datetime
from collections import namedtuple
import time, pickle

search_page = Blueprint('search', __name__)

selected_exercise = ""
display_results = False



@search_page.route("/search", methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST': #need to add more ways of searching (example: by location, city...)
        display_results = True
        target_exercise_name = request.form.get('exerciseName')
        if len(target_exercise_name)==0: #if no filters are given. Simply show all possible hotels. 
            search_results = Exercises.query.all()
        else:
            search_results = Exercises.query.filter(Exercises.name == target_exercise_name).all()
        return render_template('search.html', exercises = search_results, display_results = display_results)
    return render_template('search.html')