from . import db
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, login_required, logout_user, current_user, login_manager
from .models import User
import pickle


display_profile = Blueprint('profile', __name__)

@display_profile.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    if request.method == 'POST':
        if request.method == 'POST':
            new_goal_weight = request.form.get('newGoalWeight')
            if new_goal_weight.strip() == str(current_user.goal_weight).strip():
                flash(f'Your goal weight is already at {new_goal_weight}!', 'error')
            else:
                try:
                    current_user.goal_weight = new_goal_weight
                    db.session.commit()
                    flash('Goal weight updated successfully!', 'success')
                    return redirect(url_for('profile.user_profile'))
                except Exception:
                    flash('Faield to update your new goal weight, please try again!')
                    
    if current_user.splits:
        split_content = current_user.splits[0].content
    else: #current user has not created a split yet. 
        split_content = None

    return render_template('profile.html', 
                            name = current_user.full_name, 
                            email= current_user.email, 
                            address= current_user.address, 
                            DOR= current_user.DOR, 
                            goalWeight = current_user.goal_weight,
                            workout_split= split_content, 
                            gender = current_user.gender)




