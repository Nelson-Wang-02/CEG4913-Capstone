import cv2
import time
import os
import subprocess
import copy
import numpy as np
from datetime import datetime
from cvzone.PoseModule import PoseDetector
from bad_form import Bad_form
from frames_to_vid import build_video_from_frames 
from mocap_general import Mocap_General
from nanoSensorBLE import connector
import threading
#consts
unity_exe_path = ".\\Unity Animator Entity\\MotionCapture.exe" #need normpath here
batch_file_path = ".\\run_unity_engine_no_engine.bat"
exercise_name = "Lateral raise"

class Lateral_raise_mocap(Mocap_General):
    def __init__(self):

        #current analysis coordinates
        self.left_shoulder_coords = None #11
        self.right_shoulder_coords = None #12
        self.left_elbow_coords = None #13 
        self.right_elbow_coords = None #14
        self.left_hip_coords = None #15
        self.right_hip_coords = None #16
        self.offset_Y = None
        self.count = 0
        self.bad_form_captured = False
        self.lm_exercise_map = { 
            "Lateral raise": {
                "L shoulder": 11, 
                "R shoulder": 12, 
                "L elbow" : 13, 
                "R elbow": 14, 
                "R hip": 23,
                "L hip": 24
            }
        }
        self.bad_form_list = []
        self.bad_form = False
        self.animate_flag = False
        self.delay = 3
        self.bad_form_pics_path = os.path.join(os.getcwd(), "bad-form-bin")
        self.set_number = None
        self.env_flag = False
        self.run_time = 10 #default 10 seconds

    def run_unity_animator(self):
        try:
            subprocess.run([batch_file_path], check= True)
        except Exception as e:
            print(f"Error executing the Unity Motion Capture animation project: {e}")

        try:
            time.sleep(10.0) #replace this with more flexible way of detecting unity completion
            build_video_from_frames(fps= 30)
        except Exception as e:
            print(f"Error building video from frames in folder: {e}")

    def save_bad_form_snapshot(self, img, reason, resonsibles):
        self.bad_form_captured = True
        if self.set_number and not self.env_flag: #check if we are part of a split
            self.bad_form_pics_path = self.bad_form_pics_path + f"_setnumber{self.set_number}"
            self.env_flag = True
        if not os.path.exists(self.bad_form_pics_path):
            os.makedirs(self.bad_form_pics_path)
        time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        temp_name = f"bad_form_{self.count}_{time_stamp}.png"
        self.count +=1 #ensure uniqueness and not to write into already existing png
        filename = os.path.join(self.bad_form_pics_path, temp_name)
        if 'R' in resonsibles:
            og_y_coord_R = (self.right_shoulder_coords[1] - self.offset_Y)*(-1)
            cv2.circle(img, (self.right_shoulder_coords[0], og_y_coord_R), radius=28, color=(0, 0, 255), thickness=2)
        if 'L' in resonsibles:
            og_y_coord_L = (self.left_shoulder_coords[1] - self.offset_Y)*(-1)
            cv2.circle(img, (self.left_shoulder_coords[0], og_y_coord_L), radius=28, color=(0, 0, 255), thickness=2)
        cv2.imwrite(filename, img)
        #create bad form object
        bf = Bad_form(reason= reason, exercise_name= exercise_name, image_file_path= temp_name)
        self.bad_form_list.append(bf)

    def angle_analysis(self, img):
        #check LEFT and RIGHT side.. 
        if(
        self.left_shoulder_coords and 
        self.right_shoulder_coords and
        self.left_elbow_coords and
        self.right_elbow_coords and
        self.left_hip_coords and
        self.right_hip_coords):
            #right
            a = np.array(self.right_hip_coords)
            b = np.array(self.right_shoulder_coords)
            c = np.array(self.right_elbow_coords)
            #left
            d = np.array(self.left_hip_coords)
            e = np.array(self.left_shoulder_coords)
            f = np.array(self.left_elbow_coords)
            
            radians_R= np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
            radians_L = np.arctan2(f[1]-e[1], f[0]-e[0]) - np.arctan2(d[1]-e[1], d[0]-e[0])
            angle_R, angle_L = np.abs(radians_R*180.0/np.pi), np.abs(radians_L*180.0/np.pi)

            #adjust
            if angle_R > 180.0: 
                angle_R = 360 - angle_R
            if angle_L > 180.0:
                angle_L = 360 - angle_L

            if angle_R >= 120 or angle_L >= 120:
                reason = "" 
                responsibles = []
                if angle_R > 120:
                    reason += "Your right arm extended too high! Try to stop at a straight level.\n"
                    responsibles.append('R')
                if angle_L > 120:
                    reason += "Your left arm extended too high! Try to stop at a straight level.\n"
                    responsibles.append('L')
                if not self.bad_form_captured:
                    self.save_bad_form_snapshot(img, reason, responsibles)
                    return True
            else:
                self.bad_form_captured = False
                return False
        else:
            return(f"Not enough data yet :D")
    
    
    def run_mocap(self, run_from_split= None):
        run_flag = [True]
        
        arduino_instance = connector()

        try:
            arduino_instance.connect_arduino()
        except Exception as e: 
            print(f"Failed to connect to arduino: {e}")
            return
        
        def run_arduino_read_data():
            while run_flag[0]:
                arduino_instance.main(run_flag)


        if run_from_split:  #get options from function call
            self.run_time, self.animate_flag =  run_from_split[0], run_from_split[1]
            self.delay, self.set_number = run_from_split[2], run_from_split[3]
        #give delay
        print(f"total run time will be {self.run_time} seconds.")
        print(f"sleeping for {self.delay} seconds.")
        time.sleep(self.delay)

        #get the pertinent landmarks
        exercise_lms = list(self.lm_exercise_map.get(exercise_name, None).values())
        #landmark_coords = {id: [] for id in exercise_lms}
        #Initialize the webcam (0 is the default camera)
        cap = cv2.VideoCapture(0)

        #Initialize the PoseDetector
        detector = PoseDetector()
        analysis_queue = []
        anim_list = []

        #Get the start time
        start_time = time.time()
        frame_num = 0

        read_data_thread = threading.Thread(target=run_arduino_read_data)
        read_data_thread.start()

        while run_flag[0]:

            success, img = cap.read()
            raw_image = copy.deepcopy(img)
            if not success:
                break  # Exit the loop if the frame was not captured
            
            frame_num += 1
            #Perform pose estimation
            img = detector.findPose(img)
            lmList, bboxInfo = detector.findPosition(img)        
            #If pose information is found, store it
            if bboxInfo:
                frame_landmarks = {}
                anim_string = ''
                img_height = img.shape[0]
                self.offset_Y = img_height
                for i, lm in enumerate(lmList):
                    anim_string += f'{lm[0]}, {img_height-lm[1]},{lm[2]},'
                    if i in exercise_lms:
                        frame_landmarks[i] = (lm[0], img_height - lm[1], lm[2])
                analysis_queue.append((raw_image, frame_landmarks))
                anim_list.append(anim_string)
                
            #Close the video feed if the user presses the 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                run_flag[0] = False
            
            if time.time() - start_time > self.run_time:
                run_flag[0] = False

            #Show the live video feed with pose estimation
            cv2.imshow("Image", img)
        
        read_data_thread.join()

        with open("AnimationFileUnityData.txt", 'w') as w:
            w.writelines(["%s\n" % item for item in anim_list])


        #Release the video capture object and close OpenCV windows
        cap.release()
        cv2.destroyAllWindows()
        cooldown = 0 #skip 20 frames after badform detected
        for img, relLms in analysis_queue:
            if(cooldown == 0):
                self.left_shoulder_coords = relLms.get(11)
                self.right_shoulder_coords = relLms.get(12)
                self.left_elbow_coords = relLms.get(13)
                self.right_elbow_coords = relLms.get(14)
                self.right_hip_coords = relLms.get(23)
                self.left_hip_coords = relLms.get(24)
                saved_snap = self.angle_analysis(img)
                if(saved_snap): cooldown = 10
            else:
                cooldown -=1

        return 1

if __name__ == '__main__':
    lr = Lateral_raise_mocap()
    lr.run_mocap()
    if lr.animate_flag:
        print("Running the animator now!")
        lr.run_unity_animator()
