from flask import Flask, render_template, request, jsonify, Response, json
from flask_socketio import SocketIO, emit
from flask_cors import CORS, cross_origin
import mediapipe as mp
from tensorflow import keras
import base64
import io
from io import StringIO
from PIL import Image
import cv2
import imutils
import numpy as np
from ExerciseDecoder import mediapipe_detection, draw_landmarks, extract_keypoints, colors, prob_viz, count_reps, get_coordinates, calculate_angle, viz_joint_angle
import os
import math
app = Flask(__name__)
CORS(app)
# socketio = SocketIO(app, cors_allowed_origins="*")
mp_pose = mp.solutions.pose
GREEN_COLOR = (0, 255, 0)
RED_COLOR = (0, 0, 255)
YELLOW_COLOR = (0, 255, 255)
actions = np.array(['Bench Press','PushUp','Barbell Biceps Curl', 'Lateral Raises', 'Shoulder Press','Squat'])
model = keras.models.load_model('LSTM_Attention_128HUs.h5')
app.config['model'] = model
@app.route('/', methods=['POST', 'GET'])
def index():
    data = {"message": "hemlo"}
    json_data = json.dumps(data)
    response = Response(json_data, status=201, mimetype='application/json')
    return response

sequence = []

@app.route('/test_video', methods=['POST', 'GET'])
def test_video():
    file = request.files['file']
    
    
    frames_dir = 'frames/'
    if not os.path.exists(frames_dir):
        os.makedirs(frames_dir)

    # Define the path to save the uploaded video temporarily
    video_path = 'uploads/' + file.filename
    if not os.path.exists('uploads/'):
        os.makedirs('uploads/')
    file.save(video_path)

    # Capture the video
    global sequence
    predictions = []
    res = []
    threshold = 0.5 # minimum confidence to classify as an action/exercise
    current_action = ''
    curl_counter = 0
    press_counter = 0
    squat_counter = 0
    pushup_counter = 0
    bench_press_counter = 0
    curl_stage = None
    press_stage = None
    squat_stage = None
    pushup_stage = None
    bench_press_stage = None
    error = False
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'X264') # video compression format
    HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) # webcam video frame height
    WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) # webcam video frame width
    FPS = int(cap.get(cv2.CAP_PROP_FPS)) # webcam video fram rate 

    video_name = "output/output_video.mp4"
    out = cv2.VideoWriter(video_name, fourcc, FPS, (WIDTH, HEIGHT))
    
    sequence_length = 30
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            # print(np.shape(frame), "frame")
            if ret:
                image, results = mediapipe_detection(frame, pose)
                # print(np.shape(image), "image")
                # print(np.shape(results), "results")
                draw_landmarks(image, results)
                keypoints = extract_keypoints(results)
                # print(np.shape(keypoints), "keypoints")     
                sequence.append(keypoints)      
                sequence = sequence[-sequence_length:]
                # print(np.shape(sequence), "sequence")  
                # print(sequence)
                if len(sequence) == sequence_length:
                    res = model.predict(np.expand_dims(sequence, axis=0), verbose=0)[0]
                    predictions.append(np.argmax(res))
                    current_action = actions[np.argmax(res)]
                    print(current_action)
                    confidence = np.max(res)
                    # print(current_action)
                    if confidence < threshold:
                        current_action = ''
                    image = prob_viz(res, actions, image, colors)
                    # try:
                    landmarks = results.pose_landmarks.landmark
                    def perform_barbell_bicep_curl_pose_correction(landmarks, mp_pose):
                        # Get coordinates
                        shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
                        elbow = get_coordinates(landmarks, mp_pose, 'left', 'elbow')
                        wrist = get_coordinates(landmarks, mp_pose, 'left', 'wrist')

                        # Calculate the angle at the elbow
                        elbow_angle = calculate_angle(shoulder, elbow, wrist)

                        # Compute the distance between the wrist and shoulder
                        shoulder_to_wrist_dist = math.dist(shoulder, wrist)

                        # Define angle and distance thresholds
                        max_elbow_angle_threshold = 150  # Adjust this angle threshold as needed
                        max_distance_threshold = 0.5  # Adjust this distance threshold as needed

                        # Check elbow angle and wrist position for form correction
                        form_break = elbow_angle > max_elbow_angle_threshold or shoulder_to_wrist_dist > max_distance_threshold

                        return form_break


                    def perform_pushup_pose_correction(landmarks, mp_pose):
                        shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
                        hip = get_coordinates(landmarks, mp_pose, 'left', 'hip')

                        # Calculate the slope of the line formed by shoulder and hip points
                        shoulder_hip_slope = (hip[1] - shoulder[1]) / (hip[0] - shoulder[0] + 1e-6)  # Adding a small constant to avoid division by zero

                        # Define a threshold for the allowed slope (body should form a straight line)
                        max_slope_threshold = 0.2  # Adjust this threshold according to your specific use case

                        # Check if the slope exceeds the threshold, indicating a form break
                        form_break = abs(shoulder_hip_slope) < max_slope_threshold

                        return form_break
    
                    def perform_squat_pose_correction(landmarks, mp_pose):
                        left_hip = get_coordinates(landmarks, mp_pose, 'left', 'hip')
                        left_knee = get_coordinates(landmarks, mp_pose, 'left', 'knee')
                        left_ankle = get_coordinates(landmarks, mp_pose, 'left', 'ankle')
                        right_hip = get_coordinates(landmarks, mp_pose, 'right', 'hip')
                        right_knee = get_coordinates(landmarks, mp_pose, 'right', 'knee')
                        right_ankle = get_coordinates(landmarks, mp_pose, 'right', 'ankle')

                        # Calculate angles
                        left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
                        right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)

                        # Check knee angles and hip positions for correct squat form
                        min_knee_angle = 160  # Minimum knee angle for a proper squat (adjust as needed)
                        max_hip_height_difference = 0.1  # Maximum allowed height difference between hips during squat

                        if left_knee_angle > min_knee_angle and right_knee_angle > min_knee_angle:
                            # Check hip heights to ensure parallel squat
                            hip_height_difference = abs(left_hip[1] - right_hip[1])
                            if hip_height_difference < max_hip_height_difference:
                                return False  # Correct squat pose
                        return True  # Incorrect squat pose
    
                    def perform_bench_press_pose_correction(landmarks, mp_pose):
                        # Get coordinates for the left elbow, left shoulder, and left hip
                        left_shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
                        left_elbow = get_coordinates(landmarks, mp_pose, 'left', 'elbow')
                        left_hip = get_coordinates(landmarks, mp_pose, 'left', 'hip')

                        # Calculate the angle at the left elbow
                        elbow_angle = calculate_angle(left_shoulder, left_elbow, left_hip)

                        # Define a threshold for the allowed elbow angle
                        max_elbow_angle_threshold = 90  # Adjust this threshold according to your specific use case

                        # Check if the elbow angle exceeds the threshold
                        form_break = elbow_angle > max_elbow_angle_threshold

                        return form_break
    
                    def perform_shoulder_press_pose_correction(landmarks, mp_pose):
                        # Get coordinates for the left shoulder, left elbow, and left wrist
                        left_shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
                        left_elbow = get_coordinates(landmarks, mp_pose, 'left', 'elbow')
                        left_wrist = get_coordinates(landmarks, mp_pose, 'left', 'wrist')

                        # Calculate the angle at the left elbow
                        elbow_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)

                        # Define a threshold for the allowed elbow angle
                        max_elbow_angle_threshold = 90  # Adjust this threshold according to your specific use case

                        # Check if the elbow angle exceeds the threshold
                        form_break = elbow_angle > max_elbow_angle_threshold

                        return form_break
    
                    def perform_leg_raises_pose_correction(landmarks, mp_pose):
                        # Get coordinates for the left hip, left knee, and left ankle
                        left_hip = get_coordinates(landmarks, mp_pose, 'left', 'hip')
                        left_knee = get_coordinates(landmarks, mp_pose, 'left', 'knee')
                        left_ankle = get_coordinates(landmarks, mp_pose, 'left', 'ankle')

                        # Calculate the angle at the left hip
                        hip_angle = calculate_angle(left_hip, left_knee, left_ankle)

                        # Define a threshold for the allowed hip angle
                        min_hip_angle_threshold = 45  # Adjust this threshold according to your specific use case

                        # Check if the hip angle is below the threshold
                        form_break = hip_angle < min_hip_angle_threshold

                        return form_break
                    
                    if current_action == 'Barbell Biceps Curl': 
        # Get coords
        
                        shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
                        elbow = get_coordinates(landmarks, mp_pose, 'left', 'elbow')
                        wrist = get_coordinates(landmarks, mp_pose, 'left', 'wrist')
                        # curl_counter += 1
                        
                        # calculate elbow angle
                        angle = calculate_angle(shoulder, elbow, wrist)
                        print(angle)
                        # curl counter logic
                        if angle < 30:
                            curl_stage = "up" 
                        if angle > 140 and curl_stage =='up':
                            curl_stage="down"  
                            curl_counter +=1
                        error = perform_barbell_bicep_curl_pose_correction(landmarks, mp_pose)    
                        press_stage = None
                        squat_stage = None
                        pushup_stage = None
                        lateral_raises_stage = None
                        bench_press_stage = None
                            
                        # Viz joint angle
                        viz_joint_angle(image, angle, elbow)
                        
                    elif current_action == "PushUp":
                        # Get coordinates
                        shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
                        elbow = get_coordinates(landmarks, mp_pose, 'left', 'elbow')
                        wrist = get_coordinates(landmarks, mp_pose, 'left', 'wrist')

                        # Calculate elbow angle
                        elbow_angle = calculate_angle(shoulder, elbow, wrist)
                        print(elbow_angle)
                        # PushUp counter logic
                        if elbow_angle < 110:  # Adjust the angle as needed for your specific use case
                            pushup_stage = "down"
                        if elbow_angle > 130 and pushup_stage == "down":
                            pushup_stage = "up"
                            pushup_counter += 1
                        perform_pushup_pose_correction(landmarks, mp_pose)
                        curl_stage = None
                        press_stage = None
                        squat_stage = None
                        bench_press_stage = None
                        lateral_raises_stage = None

                        # Viz joint angle
                        viz_joint_angle(image, elbow_angle, elbow)
                        
                        
                    elif current_action == 'Shoulder Press':
                        
                        # Get coords
                        shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
                        elbow = get_coordinates(landmarks, mp_pose, 'left', 'elbow')
                        wrist = get_coordinates(landmarks, mp_pose, 'left', 'wrist')

                        # Calculate elbow angle
                        elbow_angle = calculate_angle(shoulder, elbow, wrist)
                        
                        # Compute distances between joints
                        shoulder2elbow_dist = abs(math.dist(shoulder,elbow))
                        shoulder2wrist_dist = abs(math.dist(shoulder,wrist))
                        
                        # Press counter logic
                        if (elbow_angle > 130):
                            press_stage = "up"
                        if (elbow_angle < 90) and (press_stage =='up'):
                            press_stage='down'
                            press_counter += 1
                        error = perform_shoulder_press_pose_correction(landmarks, mp_pose)
                        curl_stage = None
                        squat_stage = None
                        pushup_stage = None
                        lateral_raises_stage = None
                        bench_press_stage = None
                            
                        # Viz joint angle
                        viz_joint_angle(image, elbow_angle, elbow)
                    
                    elif current_action == "Lateral Raises":
                        # Get coordinates
                        shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
                        elbow = get_coordinates(landmarks, mp_pose, 'left', 'elbow')
                        wrist = get_coordinates(landmarks, mp_pose, 'left', 'wrist')

                        # Calculate elbow angle
                        elbow_angle = calculate_angle(shoulder, elbow, wrist)

                        # Lateral Raises counter logic
                        if elbow_angle > 90:  # Adjust the angle as needed for your specific use case
                            lateral_raises_stage = "up"
                        if elbow_angle < 45 and lateral_raises_stage == "up":
                            lateral_raises_stage = "down"
                            lateral_raises_counter += 1
                        
                        curl_stage = None
                        pushup_stage = None
                        press_stage = None
                        squat_stage = None
                        bench_press_stage = None

                        # Viz joint angle
                        viz_joint_angle(image, elbow_angle, elbow)
                        
                    elif current_action == "Bench Press":
                        # Get coordinates
                        shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
                        elbow = get_coordinates(landmarks, mp_pose, 'left', 'elbow')
                        wrist = get_coordinates(landmarks, mp_pose, 'left', 'wrist')

                        # Calculate elbow angle
                        elbow_angle = calculate_angle(shoulder, elbow, wrist)

                        # Bench Press counter logic
                        if elbow_angle > 90:  # Adjust the angle as needed for your specific use case
                            bench_press_stage = "up"
                        if elbow_angle < 45 and bench_press_stage == "up":
                            bench_press_stage = "down"
                            bench_press_counter += 1
                        error= perform_bench_press_pose_correction(landmarks, mp_pose)
                        curl_stage = None
                        pushup_stage = None
                        press_stage = None
                        squat_stage = None
                        lateral_raises_stage = None  # Assuming you don't want to count lateral raises during bench press

                        # Viz joint angle
                        viz_joint_angle(image, elbow_angle, elbow)
                        
                    elif current_action == 'Squat':
                        # Get coords
                        # left side
                        left_shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
                        left_hip = get_coordinates(landmarks, mp_pose, 'left', 'hip')
                        left_knee = get_coordinates(landmarks, mp_pose, 'left', 'knee')
                        left_ankle = get_coordinates(landmarks, mp_pose, 'left', 'ankle')
                        # right side
                        right_shoulder = get_coordinates(landmarks, mp_pose, 'right', 'shoulder')
                        right_hip = get_coordinates(landmarks, mp_pose, 'right', 'hip')
                        right_knee = get_coordinates(landmarks, mp_pose, 'right', 'knee')
                        right_ankle = get_coordinates(landmarks, mp_pose, 'right', 'ankle')
                        
                        # Calculate knee angles
                        left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
                        right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
                        
                        # Calculate hip angles
                        left_hip_angle = calculate_angle(left_shoulder, left_hip, left_knee)
                        right_hip_angle = calculate_angle(right_shoulder, right_hip, right_knee)
                        
                        # Squat counter logic
                        thr = 165
                        if (left_knee_angle < thr) and (right_knee_angle < thr) and (left_hip_angle < thr) and (right_hip_angle < thr):
                            squat_stage = "down"
                        if (left_knee_angle > thr) and (right_knee_angle > thr) and (left_hip_angle > thr) and (right_hip_angle > thr) and (squat_stage =='down'):
                            squat_stage='up'
                            squat_counter += 1
                        error = perform_squat_pose_correction(landmarks, mp_pose)
                        curl_stage = None
                        press_stage = None
                        pushup_stage = None
                        lateral_raises_stage = None
                        bench_press_stage = None
                            
                        # Viz joint angles
                        viz_joint_angle(image, left_knee_angle, left_knee)
                        viz_joint_angle(image, left_hip_angle, left_hip)
                        
                    else:
                        pass
                    
                    cv2.rectangle(image, (0,0), (1440, 40), colors[np.argmax(res)], -1)
                    cv2.putText(image, 'Curl ' + str(curl_counter), (3,30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(image, 'Press ' + str(bench_press_counter), (220,30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(image, 'Pushup ' + str(pushup_counter), (660,30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(image, 'S-Press ' + str(press_counter), (880,30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(image, 'Squat ' + str(squat_counter), (1100,30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    error_text = 'Work On Your Posture' if error else 'Form Status: Correct'
                    error_color = GREEN_COLOR if not error else YELLOW_COLOR
                    cv2.putText(image, error_text, (890, 75), cv2.FONT_HERSHEY_SIMPLEX, 1, error_color, 2, cv2.LINE_AA)
                out.write(image)   
            else:
                break
        cap.release()
        out.release()
    
    with open('output/output_video.mp4', 'rb') as video_file:
        base64_video = base64.b64encode(video_file.read()).decode('utf-8')
        
    response_data = {
        "curl_counter": curl_counter,
        "press_counter": press_counter,
        "squat_counter": squat_counter,
        "pushup_counter": pushup_counter,
        "bench_press_counter": bench_press_counter,
        "video": base64_video,
    } 
    
    return jsonify(response_data)
# @socketio.on('connect')
# def test_connect():
#     print("hemlo")

# @socketio.on('disconnect')
# def test_disconnect():
#     print('Client disconnected')

# @socketio.on("image")
# def handle_live_feed(data):
#     pass



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)