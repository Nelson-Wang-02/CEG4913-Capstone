from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, login_required, logout_user, current_user, login_manager
from . import db
from datetime import datetime
from .frames_to_vid import png_to_mp4_multithreaded
import numpy as np
import requests
import subprocess
import time
import os
import json
import zipfile
import joblib
import glob
from io import BytesIO

start_exercise = Blueprint('start_exercise', __name__)
batch_file_path = os.getcwd() + "\\Website\\run_unity_engine_no_engine.bat"
video_name = None
cal_predict_model = joblib.load(os.path.join(os.getcwd(), "Website", "ML", "calorie_predictor_model.pkl"))
scaler = joblib.load(os.path.join(os.getcwd(), "Website", "ML", "scaler.pkl"))

def stall_for_unity(folder_path):
    completion_path = os.path.join(folder_path, "completion.txt")
    while not(os.path.exists(completion_path)):
        time.sleep(1)

def get_fps(total_duration, num_frames):
    print("NUM FRAMES: ", num_frames, "TOTAL DURATION: ",total_duration)
    return int(num_frames/int(total_duration)) #round

def run_unity_animator(duration, number_of_frames):
    try:
        path_to_exe = os.path.join(os.getcwd(), 'Website', 'animation', 'MotionCapture.exe')
        print(path_to_exe)
        subprocess.run([batch_file_path, path_to_exe], check= True)
    except Exception as e:
        print(f"Error executing the Unity Motion Capture animation project: {e}")

    try:
        input_folder = os.getcwd() + '\\Website\\animation\\MotionCapture_Data\\Animation Frames'
        stall_for_unity(input_folder)
        time_now = datetime.now().strftime("%Y%m%d_%H%M%S")
        vid_name = f"animation_{time_now}_.mp4"
        output_folder_ = os.getcwd() + f'\\Website\\static\\Animation Results\\'
        output_folder = os.getcwd() + f'\\Website\\static\\Animation Results\\{vid_name}'
        if not(os.path.exists(output_folder_)):
            os.mkdir(output_folder_)
        target_fps = get_fps(duration, number_of_frames)
        png_to_mp4_multithreaded(input_folder, output_folder, fps= target_fps)
        return vid_name
    except Exception as e:
        print(f"Error building video from frames in folder: {e}")
        return None

def send_script_request_to_pi(exercise_name, delay, duration, animate_flag, exercise_list):
    url = "http://172.20.10.4:5000/run_script"
    #TODO: Get fields from the front end through user input.
    #TODO: Integrate different payload if split is launched instead of just one exercise.
    payload = {
        "exercise_list": exercise_list,
        "script_name": exercise_name,
        "delay": delay, #s
        "time": duration, #s
        "animate": animate_flag, #default
    }
    try:
        response = requests.post(url, json= payload)
    except Exception as e:
        print(f"Failed to communicate with pi server: {e}")
        response  = None
        return None
    directory_path = os.path.join(os.getcwd(), "Website", "animation", "MotionCapture_Data")
    image_path = os.path.join(os.getcwd(), "Website", "static", "Snapshots")
    os.makedirs(image_path, exist_ok=True)
    if response and response.status_code == 200:
        num_reps = int(response.headers.get('Num-Reps'))
        avg_bpm = int(float(response.headers.get('Avg-BPM')))
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            for file in z.namelist():
                if file=="AnimationFileUnityData.txt":
                    coord_file_name = os.path.join(directory_path, "AnimationFileUnityData.txt")
                    with open(coord_file_name, 'wb') as f:
                        f.write(z.read(file))
                    print(f"File saved as {coord_file_name}")
                elif file == "bad_form_data.json":
                    file_name = os.path.join(image_path, "bad_form_data.json")
                    with open(file_name, 'wb') as j:
                        j.write(z.read(file))
                    print(f"JSON saved as {file_name}")
                elif file.endswith(".png"):
                    png_path = os.path.join(image_path, os.path.basename(file))
                    with open(png_path, 'wb') as f:
                        f.write(z.read(file))
                    print(f"Snapshot extracted to {png_path}")
        with open(coord_file_name, 'r') as f:
            line_count = len(f.readlines())
        if animate_flag:
            video_name = run_unity_animator(duration, line_count)
            return (video_name, num_reps, avg_bpm)
    else:
        return response.json().get("output", "Error, no response from pi server")

def get_age(uDOB) -> int:
    birth_date = datetime.strptime(uDOB, "%Y-%m-%d")
    current_date = datetime.now()
    age = current_date.year - birth_date.year
    if(current_date.month, current_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age

def score(num_reps, num_bad_form):
    good_reps = num_reps - num_bad_form
    if(good_reps < 0): #protect negative reps
        good_reps = 0
    if(num_reps == 0):#protect div by 0
        grade = 0
    else:
        grade = int((good_reps/num_reps)*100)
    if( 0 <= grade <= 49): letter_grade = "F"
    elif(50 <= grade <= 59): letter_grade = "D"
    elif(60 <= grade <= 63): letter_grade = "C-"
    elif(64 <= grade <= 65): letter_grade = "C"
    elif(66 <= grade <= 69): letter_grade = "C+"
    elif(70 <= grade <= 73): letter_grade = "B-"
    elif(74 <= grade <= 75): letter_grade = "B"
    elif(76 <= grade <= 79): letter_grade = "B+"
    elif(80 <= grade <= 84): letter_grade = "A-"
    elif(85 <= grade <= 89): letter_grade = "A"
    elif(90 <= grade): letter_grade = "A+"
    else: letter_grade = "F"
    return (grade, letter_grade, good_reps) 

def get_user_grades():
    #print(current_user.grades)
    return current_user.grades

def add_grade_to_user(grade):
    try:
        temp_user_grades = current_user.grades[:]
        if(len(temp_user_grades) >=20): temp_user_grades.pop(0) #remove oldest grade in user history
        temp_user_grades.append(float(grade))
        current_user.grades = temp_user_grades
        db.session.flush()
        db.session.commit()
    except Exception as e:
        print(f"Failed to operate on user grade history {e}")
    
@start_exercise.route("/start", methods=["GET", "POST"])
def start_page():
    if request.method == 'POST':
        snapshots_folder = os.path.join(os.getcwd(),'Website','static', 'Snapshots')
        files=  glob.glob(snapshots_folder+"/*") #cleanse the snapshots folder. 
        print(f"removing {len(files)} snapshots.")

        try:
            for f in files:
                os.remove(f)
        except Exception as e:
            print(f"Failed to remove the lingering snapshots. Please remove them manually.{e}")
        print(request.form)
        exercise_delay = request.form['delay']
        exercise_duration = request.form['duration']
        exercise_animate = request.form.get('animate') == 'on' #true if checked, flase otherwise.
        exercise_name = request.form['exercise_name']
        #print(exercise_name, exercise_delay, exercise_duration, exercise_animate)
        #wrap in try to not crash website... 
        res = send_script_request_to_pi(exercise_name, exercise_delay, exercise_duration, exercise_animate, [])
        if not res: #no response from pi. 
            print("Failed to get resposne from pi side")
            flash("Failed to get resposne from pi side", category="error")
            return render_template("home.html")
        video_name, number_of_reps, user_average_bpm = res[0], res[1], res[2]
        snapshots_dir = os.path.join(os.getcwd(),'Website', 'static', 'Snapshots')
        # Get list of PNG files in the folder
        png_files = [file for file in os.listdir(snapshots_dir) if file.endswith('.png')]
        #get bad form desciptions from json
        descriptions = {}
        json_file_path = os.path.join(snapshots_dir, "bad_form_data.json")
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as f:
                descriptions = json.load(f)
        user_weight = current_user.current_weight
        user_height = current_user.current_height
        user_age = get_age(current_user.date_of_birth)
        if(current_user.gender == 'male' or current_user.gender == 'other'):
            user_gender = 0 #default male
        else:
            user_gender = 1   #place holder untill we get sensor data
        intensity = 1 #default untill we have a way to set this
        input_data = np.array([[user_gender, 
                                user_age, 
                                user_height, 
                                user_weight, 
                                int(exercise_duration)/60, 
                                user_average_bpm, 
                                intensity]])
        scaled_input = scaler.transform(input_data)
        predicted_calories = cal_predict_model.predict(scaled_input)
        #print("Predicted Cals: ", predicted_calories)
        #print("# reps : ", number_of_reps)
        number_bad_reps = len(png_files)
        sb_total = score(number_of_reps, number_bad_reps)
        add_grade_to_user(sb_total[0])
        user_grades = get_user_grades()
        #print(sb_total)
    return render_template('start_exercise.html', vid_name= video_name, png_files= png_files, descriptions=descriptions, cals = predicted_calories, avg_bpm = user_average_bpm, user_grades = user_grades,
                            perc_grade = sb_total[0], let_grade = sb_total[1], good_reps = sb_total[2], total_reps = number_of_reps, bad_reps= number_bad_reps) #TODO: default to 10  change when rep detect ready


@start_exercise.route("/start-split", methods=["GET", "POST"])
def start_split_page():
    #fetch the current set of exercises to launch based on user's split. 
    #this page is not attainable if a user does not have a split, so no need to null check it. 
    current_user_split = current_user.splits[0].content
    current_day = datetime.now().strftime("%A") #returns string of weekday name (i.e "Wednesday")
    exercise_list_for_today = current_user_split.get(current_day, None)
    print(exercise_list_for_today)
    if exercise_list_for_today: #if not rest...
        is_rest = False
        send_script_request_to_pi("", 10, 10, "false", exercise_list_for_today)
    else:
        is_rest = True
    return render_template('start_split.html', rest_flag = is_rest)

@start_exercise.route("/exercise", methods=['GET', 'POST'])
def exercise_landing_page():
    if request.method == 'POST':
        exercise_name = request.form['exercise_name']
    return render_template('exercise_landing.html', exercise_name= exercise_name)






