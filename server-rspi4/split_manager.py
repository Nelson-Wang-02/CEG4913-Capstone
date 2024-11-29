import time
from mocap_shoulder_press import Shoulder_press_mocap
from mocap_lateral_raise import Lateral_raise_mocap
from mocap_curl import Curl_mocap

class splitManager():
    """
    INPUT: POST Request payload ( forwarded from pi4 FLASK server )... 
    - > Payload: [...Exercise names]
        example: ["Shoulder-Press", "Lateral-Raise",...]

    Responsible for iterating over these script names and calling them in order. 
        -> Manage files and resources for accessed by these scripts. 
    """
    def __init__(self, exercise_list, desired_delay = 20):
        #for simplicity... When running exercices in batch through here, the options will be defaulted. 
        #maybe later we can add a way to customize options like delay before camera starts, and potentially exercises should be animated
        #through the script launch options defined in mocap_general.py [--time, --delay, --a, --setnum] etc... 
        self.exercise_list = exercise_list
        self.delay_between_exercices = desired_delay #seconds (maybe allow user to set this in web app)

    def launch_exercise_chain(self):
        set_number = 1 #track the set number... 
        run_time = 10 #seconds
        animate_flag = False #set to true if user wants (through web app/payload)
        delay = 3
        for exercise_name in self.exercise_list: #iterate over payload exercise name
            match exercise_name:
                #run_time, self.animate_flag, self.delay, self.set_number
                case "Shoulder Press":
                    shp = Shoulder_press_mocap()
                    shp.run_mocap(run_from_split= (run_time, animate_flag, delay, set_number))
                    if shp.animate_flag:
                        print("Running the animator now!")
                        shp.run_unity_animator() 
                case "Bicep Curl":
                    bic = Curl_mocap()
                    bic.run_mocap(run_from_split= (run_time, animate_flag, delay, set_number))
                    if bic.animate_flag:
                        print("Running the animator now!")
                        bic.run_unity_animator() 
                case "Lateral Raise":
                    lar = Lateral_raise_mocap()
                    lar.run_mocap(run_from_split= (run_time, animate_flag, delay, set_number))
                    if lar.animate_flag:
                        print("Running the animator now!")
                        lar.run_unity_animator() 
                case _:
                    print(f"Exercise : {exercise_name} not supported yet :(")
                    continue #skip rest... 
            time.sleep(self.delay_between_exercices) #idle delay between exercises
            set_number += 1 #increment set number before next exercise

if __name__ == "__main__":
    sm = splitManager(exercise_list=["Shoulder Press", "Lateral Raise"], desired_delay = 10)
    sm.launch_exercise_chain()






