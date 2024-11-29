from . import db
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, login_required, logout_user, current_user, login_manager
from .models import User, Split
from datetime import datetime
import pickle


splits_page = Blueprint('splits', __name__)

@splits_page.route('/splits', methods=['GET', 'POST'])
@login_required
def splits():
    return render_template('splits.html')

@splits_page.route('/create_splits', methods=['POST'])
@login_required
def create_splits():
    if request.method == 'POST':
        split_data = request.get_json()  
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        split_id  = f"{current_user.id}_{current_time}"
        existing_split = Split.query.filter_by(user_id=current_user.id).first()

        if existing_split:
            existing_split.split_ID = split_id
            existing_split.content = split_data
            db.session.commit()
            flash('Workout split updated successfully!', 'success')
        else:
            new_split = Split(
                split_ID=split_id,
                split_name=f"Split_{current_time}", 
                user_id=current_user.id,
                content=split_data 
            )
            try:
                db.session.add(new_split)
                db.session.commit()
                flash('Workout split created successfully!', 'success')

            except Exception as e:
                flash('Failed to create split. Try again.', 'error')
        return redirect(url_for('splits.splits')) #refresh page? maybe not needed...




