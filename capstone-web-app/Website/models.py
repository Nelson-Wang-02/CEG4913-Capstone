from . import db
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
import pickle
from sqlalchemy import JSON

Base = declarative_base()

class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id = db.Column(db.String(255), primary_key= True) #PK
    full_name = db.Column(db.String(255))
    gender = db.Column(db.String(255)) 
    email = db.Column(db.String(255), unique= True)
    password = db.Column(db.String(255))
    address = db.Column(db.String(255))
    date_of_birth = db.Column(db.String(255))
    current_weight = db.Column(db.Float)
    current_height = db.Column(db.Float)
    goal_weight = db.Column(db.Float)
    goal_str = db.Column(db.String(255))
    DOR = db.Column(db.String(255))
    grades = db.Column(JSON, default=[])
    # Relationship to splits
    splits = db.relationship('Split', backref='user', lazy=True)


class Split(db.Model):
    __tablename__ = 'Split'
    split_ID = db.Column(db.String(255), primary_key= True)
    split_name = db.Column(db.String(255), unique= True)
    user_id = db.Column(db.String(255), db.ForeignKey('User.id'), nullable=False)
    content = db.Column(JSON, nullable=False, default={})


class Exercises(db.Model):
    __tablename__ = 'Exercises'
    exercise_ID = db.Column(db.Integer, primary_key= True)
    name = db.Column(db.String(255), unique= True)
    level = db.Column(db.String(255))
    description = db.Column(db.String(255))
    image_resource_path = db.Column(db.String(255))