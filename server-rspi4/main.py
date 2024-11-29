from flask import Flask, request, jsonify, send_file
import subprocess
import os
import zipfile  
import json

#customs
from mocap_shoulder_press import Shoulder_press_mocap
from mocap_lateral_raise import Lateral_raise_mocap
from mocap_curl import Curl_mocap
from split_manager import splitManager
from rep_counter import rep_counter

app = Flask(__name__)



def build_json(bf_list):
    json_path = os.path.join(os.getcwd(), "bad_form_data.json")
    content = {}
    for bf in bf_list:
        content[bf.image_file] = bf.reason
    with open(json_path, 'w') as f:
        json.dump(content, f)
        
def run_script_(payload) -> int: #check returns on this function to see how we return the results to web app.
    default_filename = "IMU_data.csv"
    exercise_list = payload.get('exercise_list', []) #default will be empty list if not specified #truthy if is a split, falsy if not a split
    has_bad_form = False
    if exercise_list: #if payload is a split call (multiple exercises incoming)
        split_manager = splitManager(exercise_list)
        split_manager.launch_exercise_chain() 

    else: #this is for single exercise runs
        script_name = payload.get('script_name', None)
        delay = int(payload.get('delay', 3)) #default delay will be 3 seconds if not given
        run_time = int(payload.get('time', 10)) #default run time will be 10 seconds if not given. 
        #animate_flag = payload.get('animate', False) #default will be false if not specified.
        #if not script_name:
        #    return jsonify({"error": "Missing 'script_name' in request"}), 400
        match script_name:
            case "Shoulder Press":
                shp = Shoulder_press_mocap()
                shp.run_time, shp.delay = run_time, delay
                shp.run_mocap()
                if shp.bad_form_list:
                    build_json(shp.bad_form_list)
                if shp.animate_flag:
                    print("Running the animator now!")
                    shp.run_unity_animator() 
                rep_count = rep_counter(CAT='Shoulder', file_name=default_filename)
                res = rep_count.run_peak_detection(verbose=False)
                num_reps, avg_bpm = res[0], res[1]
                print(num_reps, avg_bpm)
                return (num_reps, avg_bpm)
            case "Lateral Raise":
                lar = Lateral_raise_mocap()
                lar.run_time, lar.delay = run_time, delay
                lar.run_mocap()                
                if lar.bad_form_list:
                    build_json(lar.bad_form_list)
                if lar.animate_flag:
                    print("Running the animator now!")
                    lar.run_unity_animator() 
                rep_count = rep_counter(CAT='latraise', file_name=default_filename)
                res = rep_count.run_peak_detection(verbose=False)
                num_reps, avg_bpm = res[0], res[1]
                print(num_reps, avg_bpm)
                return (num_reps, avg_bpm)
            case "Bicep Curl":
                bic = Curl_mocap()
                bic.run_time, bic.delay = run_time, delay
                bic.run_mocap()                
                if bic.bad_form_list:
                    build_json(bic.bad_form_list)
                if bic.animate_flag:
                    print("Running the animator now!")
                    bic.run_unity_animator() 
                rep_count = rep_counter(CAT='Curl', file_name=default_filename)
                res = rep_count.run_peak_detection(verbose=False)
                num_reps, avg_bpm = res[0], res[1]
                print(num_reps, avg_bpm)
                return (num_reps, avg_bpm)
            #add new scripts here
            case _:
                return None

@app.route('/run_script', methods=['POST'])
def run_script():
    if not request.is_json:
        return jsonify({"error": "Invalid request format, JSON expected"}), 400
    
    data = request.get_json()
    #assuming we are getting payload along this format
    """
    payload = {script_name: name, delay: 4, time: 10,  animate: True,  etc... }}
    """
    print(data)
    res = run_script_(payload= data)
    if(res):
        num_reps, avg_bpm = res[0], res[1]
    else:
        num_reps, avg_bpm = 0, 0
    #file_path = os.getcwd() + "\\AnimationFileUnityData.txt"
    zip_file_path = os.path.join(os.getcwd(), "animation_data.zip")
    bad_form_bin_path = os.path.join(os.getcwd(), "bad-form-bin")
    
    if not os.path.exists(bad_form_bin_path):
        os.makedirs(bad_form_bin_path)

    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        #Add the AnimationFileUnityData.txt
        zipf.write("AnimationFileUnityData.txt", arcname="AnimationFileUnityData.txt")
        #Add the bad form json stuff
        zipf.write("bad_form_data.json", arcname= "bad_form_data.json")

        #Add all PNG files from "bad form bin" folder
        for root, dirs, files in os.walk(bad_form_bin_path):
            for file in files:
                if file.endswith(".png"):
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, arcname=os.path.join("bad-form-bin", file))
    #Send the zip file
    response = send_file(zip_file_path, as_attachment=True)
    response.headers['Num-Reps'] = str(num_reps)
    response.headers['Avg-BPM'] = str(avg_bpm)

    #Delete all PNG files in "bad form bin" folder after sending the response
    for file in os.listdir(bad_form_bin_path):
        file_path = os.path.join(bad_form_bin_path, file)
        if file.endswith(".png"):
            os.remove(file_path)
    return response

if __name__ == '__main__':
    app.run(host='172.20.10.4', port=5000)
