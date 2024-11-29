from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, login_required, logout_user, current_user, login_manager
from . import db

from datetime import datetime
from collections import namedtuple
import time, pickle

home_page = Blueprint('home_page', __name__)

@home_page.route("/home", methods=['GET', 'POST'])#decorator
def home():
    return render_template('home.html')