#!/usr/bin/env python
# coding: utf-8

# # 0. Import Dependencies

# In[1]:


import cv2
import numpy as np
import os
from matplotlib import pyplot as plt
import time
import mediapipe as mp
import tensorflow
from tensorflow import keras
import math

from sklearn.model_selection import train_test_split
from sklearn.metrics import multilabel_confusion_matrix, accuracy_score, classification_report
from keras.utils import to_categorical

 
from keras import backend as K
from keras.callbacks import TensorBoard, EarlyStopping, ReduceLROnPlateau, ModelCheckpoint

from keras.models import Sequential, Model

from keras.layers import (LSTM, Dense, Concatenate, Attention, Dropout, Softmax,
                                     Input, Flatten, Activation, Bidirectional, Permute, multiply, 
                                     ConvLSTM2D, MaxPooling3D, TimeDistributed, Conv2D, MaxPooling2D)

from scipy import stats

# disable some of the tf/keras training warnings 
os.environ['TF_CPP_MIN_LOG_LEVEL'] = "3"
tensorflow.get_logger().setLevel("ERROR")
tensorflow.autograph.set_verbosity(1)

# suppress untraced functions warning
import absl.logging
absl.logging.set_verbosity(absl.logging.ERROR)


# In[ ]:





# # 1. Keypoints using MP Pose

# In[2]:


# Pre-trained pose estimation model from Google Mediapipe
mp_pose = mp.solutions.pose

# Supported Mediapipe visualization tools
mp_drawing = mp.solutions.drawing_utils


# In[3]:


def mediapipe_detection(image, model):
    """
    This function detects human pose estimation keypoints from webcam footage
    
    """
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) # COLOR CONVERSION BGR 2 RGB
    image.flags.writeable = False                  # Image is no longer writeable
    results = model.process(image)                 # Make prediction
    image.flags.writeable = True                   # Image is now writeable 
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) # COLOR COVERSION RGB 2 BGR
    return image, results


# In[4]:


def draw_landmarks(image, results):
    """
    This function draws keypoints and landmarks detected by the human pose estimation model
    
    """
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), 
                                mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2) 
                                 )


# In[8]:


# cap = cv2.VideoCapture(0) # camera object
# HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) # webcam video frame height
# WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) # webcam video frame width
# FPS = int(cap.get(cv2.CAP_PROP_FPS)) # webcam video fram rate 

# # Set and test mediapipe model using webcam
# with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
#     while cap.isOpened():

#         # Read feed
#         ret, frame = cap.read()
#         print(np.shape(frame))
#         print(frame)
#         print("====================================")
      
#         # Make detection
#         image, results = mediapipe_detection(frame, pose)
        
#         # Extract landmarks
#         try:
#             landmarks = results.pose_landmarks.landmark
#         except:
#             pass
        
#         # Render detections
#         draw_landmarks(image, results)               
        
#         # Display frame on screen
#         cv2.imshow('OpenCV Feed', image)
        
#         # Exit / break out logic
#         if cv2.waitKey(10) & 0xFF == ord('q'):
#             break

#     cap.release()
#     cv2.destroyAllWindows()


# # 2. Extract Keypoints

# In[6]:


# Recollect and organize keypoints from the test
# pose = []
# for res in results.pose_landmarks.landmark:
#     test = np.array([res.x, res.y, res.z, res.visibility])
#     pose.append(test)


# In[7]:


# 33 landmarks with 4 values (x, y, z, visibility)
# num_landmarks = len(landmarks)
# num_values = len(test)
# num_input_values = num_landmarks*num_values
# num_input_values


# In[8]:


# This is an example of what we would use as an input into our AI models
# pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33*4)


# In[9]:


def extract_keypoints(results):
    """
    Processes and organizes the keypoints detected from the pose estimation model 
    to be used as inputs for the exercise decoder models
    
    """
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33*4)
    return pose


# # 3. Setup Folders for Collection

# In[10]:


# Path for exported data, numpy arrays
DATA_PATH = os.path.join(os. getcwd(),'data') 
print(DATA_PATH)

# make directory if it does not exist yet
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

# Actions/exercises that we try to detect
actions = np.array(['Bench Press','PushUp','Barbell Biceps Curl', 'Lateral Raises', 'Shoulder Press','Squat'])
# actions = np.array(['squat'])
num_classes = len(actions)

# How many videos worth of data
no_sequences = 13

# Videos are going to be this many frames in length
# sequence_length = FPS*1

# Folder start
# Change this to collect more data and not lose previously collected data
start_folder = 101


# In[12]:


# # Build folder paths
# for action in actions:     
#     for sequence in range(start_folder,no_sequences+start_folder):
#         try: 
#             os.makedirs(os.path.join(DATA_PATH, action, str(sequence)))  
#         except:
#             pass


# In[20]:


# import os
# import cv2

# # Directory containing video files
# video_folder = "squat"  # Replace with the actual folder path

# # Output video file name
# output_video_file = "squats.mp4"

# # List to store video files in the folder
# video_files = []

# # Get a list of video files in the folder
# for filename in os.listdir(video_folder):
#     if filename.endswith(".mp4") or filename.endswith(".avi"):
#         video_files.append(os.path.join(video_folder, filename))

# # Check if there are video files to combine
# if not video_files:
#     print("No video files found in the folder.")
# else:
#     # Get the properties of the first video file to use as a template
#     first_video = cv2.VideoCapture(video_files[0])
#     frame_width = int(first_video.get(3))
#     frame_height = int(first_video.get(4))

#     # Define the codec and create a VideoWriter object
#     fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You can change the codec as needed
#     out = cv2.VideoWriter(output_video_file, fourcc, 30.0, (frame_width, frame_height))

#     # Iterate through video files and combine them
#     for video_file in video_files:
#         video = cv2.VideoCapture(video_file)
#         while True:
#             ret, frame = video.read()
#             if not ret:
#                 break
#             out.write(frame)

#         video.release()

#     out.release()
#     print(f"Combined video saved as {output_video_file}")
# no need of this code 


# # 4. Collect Keypoint Values for Training and Testing

# In[12]:


# Colors associated with each exercise (e.g., curls are denoted by blue, squats are denoted by orange, etc.)
colors = [(245,117,16), (117,245,16), (16,117,245),(255,0,255),(0,255,255),(255,255,0)]


# # 5. Preprocess Data and Create Labels/Features

# In[13]:


label_map = {label:num for num, label in enumerate(actions)}


# In[14]:


# Load and organize recorded training data
# sequences, labels = [], []
# for action in actions:
#     for sequence in np.array(os.listdir(os.path.join(DATA_PATH, action))).astype(int):
#         window = []
#         for frame_num in range(sequence_length):         
#             # LSTM input data
#             res = np.load(os.path.join(DATA_PATH, action, str(sequence), "{}.npy".format(frame_num)))
#             window.append(res)  
            
#         sequences.append(window)
#         labels.append(label_map[action])


# In[15]:


# Make sure first dimensions of arrays match
# X = np.array(sequences)
# y = to_categorical(labels).astype(int)
# print(X.shape, y.shape)


# In[16]:


# Split into training, validation, and testing datasets
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.10, random_state=1)
# print(X_train.shape, y_train.shape)
# X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=15/90, random_state=2)


# # 6. Build and Train Neural Networks

# In[17]:


# Callbacks to be used during neural network training 
# es_callback = EarlyStopping(monitor='val_loss', min_delta=5e-4, patience=10, verbose=0, mode='min')
# lr_callback = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=0.00001, verbose=0, mode='min')
# chkpt_callback = ModelCheckpoint(filepath=DATA_PATH, monitor='val_loss', verbose=0, save_best_only=True, 
#                                  save_weights_only=False, mode='min', save_freq=1)

# # Optimizer
# opt = tensorflow.keras.optimizers.legacy.Adam(learning_rate=0.01)

# # some hyperparamters
# batch_size = 32
# max_epochs = 500


# ## 6a. LSTM

# In[18]:


# Set up Tensorboard logging and callbacks
# NAME = f"ExerciseRecognition-LSTM-{int(time.time())}"
# log_dir = os.path.join(os.getcwd(), 'logs', NAME,'')
# tb_callback = TensorBoard(log_dir=log_dir)

# callbacks = [tb_callback, es_callback, lr_callback, chkpt_callback]


# # In[19]:


# num_input_values


# In[20]:


# lstm = Sequential()
# lstm.add(LSTM(128, return_sequences=True, activation='relu', input_shape=(sequence_length, num_input_values)))
# lstm.add(LSTM(256, return_sequences=True, activation='relu'))
# lstm.add(LSTM(128, return_sequences=False, activation='relu'))
# lstm.add(Dense(128, activation='relu'))
# lstm.add(Dense(64, activation='relu'))
# lstm.add(Dense(actions.shape[0], activation='softmax'))
# print(lstm.summary())


# In[21]:


# lstm.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['categorical_accuracy'])
# lstm.fit(X_train, y_train, batch_size=batch_size, epochs=max_epochs, validation_data=(X_val, y_val), callbacks=callbacks)


# ## 6b. LSTM + Attention

# In[22]:


# Set up Tensorboard logging and callbacks
# NAME = f"ExerciseRecognition-AttnLSTM-{int(time.time())}"
# log_dir = os.path.join(os.getcwd(), 'logs', NAME,'')
# tb_callback = TensorBoard(log_dir=log_dir)

# callbacks = [tb_callback, es_callback, lr_callback, chkpt_callback]


# In[23]:


def attention_block(inputs, time_steps):
    """
    Attention layer for deep neural network
    
    """
    # Attention weights
    a = Permute((2, 1))(inputs)
    a = Dense(time_steps, activation='softmax')(a)
    
    # Attention vector
    a_probs = Permute((2, 1), name='attention_vec')(a)
    
    # Luong's multiplicative score
    output_attention_mul = multiply([inputs, a_probs], name='attention_mul') 
    
    return output_attention_mul


# In[24]:


# HIDDEN_UNITS = 256

# # Input
# inputs = Input(shape=(sequence_length, num_input_values))

# # Bi-LSTM
# lstm_out = Bidirectional(LSTM(HIDDEN_UNITS, return_sequences=True))(inputs)

# # Attention
# attention_mul = attention_block(lstm_out, sequence_length)
# attention_mul = Flatten()(attention_mul)

# # Fully Connected Layer
# x = Dense(2*HIDDEN_UNITS, activation='relu')(attention_mul)
# x = Dropout(0.5)(x)

# # Output
# x = Dense(actions.shape[0], activation='softmax')(x)

# # Bring it all together
# AttnLSTM = Model(inputs=[inputs], outputs=x)
# print(AttnLSTM.summary())


# In[25]:


# AttnLSTM.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['categorical_accuracy'])
# AttnLSTM.fit(X_train, y_train, batch_size=batch_size, epochs=max_epochs, validation_data=(X_val, y_val), callbacks=callbacks)


# In[26]:


# Model map
# models = {
#     'LSTM': lstm, 
#     'LSTM_Attention_128HUs': AttnLSTM, 
# }


# # 7a. Save Weights

# In[34]:


# for model_name, model in models.items():
#     save_dir = os.path.join(os.getcwd(), f"{model_name}.h5")
#     model.save(save_dir)


# # 7b. Load Weights

# In[35]:


# # Run model rebuild before doing this
# for model_name, model in models.items():
#     load_dir = os.path.join(os.getcwd(), f"{model_name}.h5")
#     model.load_weights(load_dir)


# # 8. Make Predictions

# In[27]:


# for model in models.values():
#     res = model.predict(X_test, verbose=0)   


# # 9. Evaluations using Confusion Matrix and Accuracy

# In[41]:


eval_results = {}
eval_results['confusion matrix'] = None
eval_results['accuracy'] = None
eval_results['precision'] = None
eval_results['recall'] = None
eval_results['f1 score'] = None

confusion_matrices = {}
classification_accuracies = {}   
precisions = {}
recalls = {}
f1_scores = {} 


# ## 9a. Confusion Matrices

# In[20]:


# for model_name, model in models.items():
#     yhat = model.predict(X_test, verbose=0)
    
#     # Get list of classification predictions
#     ytrue = np.argmax(y_test, axis=1).tolist()
#     yhat = np.argmax(yhat, axis=1).tolist()
    
#     # Confusion matrix
#     confusion_matrices[model_name] = multilabel_confusion_matrix(ytrue, yhat)
#     print(f"{model_name} confusion matrix: {os.linesep}{confusion_matrices[model_name]}")

# # Collect results 
# eval_results['confusion matrix'] = confusion_matrices


# ## 9b. Accuracy

# In[30]:


# for model_name, model in models.items():
#     yhat = model.predict(X_test, verbose=0)
    
#     # Get list of classification predictions
#     ytrue = np.argmax(y_test, axis=1).tolist()
#     yhat = np.argmax(yhat, axis=1).tolist()
    
#     # Model accuracy
#     classification_accuracies[model_name] = accuracy_score(ytrue, yhat)    
#     print(f"{model_name} classification accuracy = {round(classification_accuracies[model_name]*100,3)}%")

# # Collect results 
# eval_results['accuracy'] = classification_accuracies


# ## 9c. Precision, Recall, and F1 Score

# In[31]:


# for model_name, model in models.items():
#     yhat = model.predict(X_test, verbose=0)
    
#     # Get list of classification predictions
#     ytrue = np.argmax(y_test, axis=1).tolist()
#     yhat = np.argmax(yhat, axis=1).tolist()
    
#     Precision, recall, and f1 score
#     report = classification_report(ytrue, yhat, target_names=actions, output_dict=True)
    
#     precisions[model_name] = report['weighted avg']['precision']
#     recalls[model_name] = report['weighted avg']['recall']
#     f1_scores[model_name] = report['weighted avg']['f1-score'] 
   
#     print(f"{model_name} weighted average precision = {round(precisions[model_name],3)}")
#     print(f"{model_name} weighted average recall = {round(recalls[model_name],3)}")
#     print(f"{model_name} weighted average f1-score = {round(f1_scores[model_name],3)}\n")

# # Collect results 
# eval_results['precision'] = precisions
# eval_results['recall'] = recalls
# eval_results['f1 score'] = f1_scores


# # 10. Choose Model to Test in Real Time

# In[21]:


# model = AttnLSTM
model_name = 'AttnLSTM'


# In[24]:


model_name = 'AttnLSTM'


# In[ ]:





# In[ ]:





# In[11]:


from tensorflow import keras


# In[22]:


# model = keras.models.load_model("LSTM_Attention_128HUs.h5")


# In[ ]:





# In[ ]:





# # 11. Calculate Joint Angles & Count Reps

# In[13]:


def calculate_angle(a,b,c):
    """
    Computes 3D joint angle inferred by 3 keypoints and their relative positions to one another
    
    """
    a = np.array(a) # First
    b = np.array(b) # Mid
    c = np.array(c) # End
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle >180.0:
        angle = 360-angle
        
    return angle 


# In[14]:


def get_coordinates(landmarks, mp_pose, side, joint):
    """
    Retrieves x and y coordinates of a particular keypoint from the pose estimation model
         
     Args:
         landmarks: processed keypoints from the pose estimation model
         mp_pose: Mediapipe pose estimation model
         side: 'left' or 'right'. Denotes the side of the body of the landmark of interest.
         joint: 'shoulder', 'elbow', 'wrist', 'hip', 'knee', or 'ankle'. Denotes which body joint is associated with the landmark of interest.
    
    """
    coord = getattr(mp_pose.PoseLandmark,side.upper()+"_"+joint.upper())
    x_coord_val = landmarks[coord.value].x
    y_coord_val = landmarks[coord.value].y
    return [x_coord_val, y_coord_val]            


# In[15]:


def viz_joint_angle(image, angle, joint):
    """
    Displays the joint angle value near the joint within the image frame
    
    """
    cv2.putText(image, str(int(angle)), 
                   tuple(np.multiply(joint, [640, 480]).astype(int)), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
                        )
    return


# In[16]:


def count_reps(image, current_action, landmarks, mp_pose):
    """
    Counts repetitions of each exercise. Global count and stage (i.e., state) variables are updated within this function.
    
    """

    curl_counter = 0
    press_counter=0
    squat_counter=0
    pushup_counter=0
    bench_press_counter=0
    curl_stage = None
    press_stage = None
    squat_stage = None
    pushup_stage = None
    bench_press_stage = None
    
    



# In[67]:


# def count_reps(image, current_action, landmarks, mp_pose):
#     """
#     Counts repetitions of each exercise. Global count and stage (i.e., state) variables are updated within this function.
    
#     """

#     global curl_counter, press_counter, squat_counter, curl_stage, press_stage, squat_stage
    
#     if current_action == 'Barbell Biceps Curl':
#         # Get coords
#         shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
#         elbow = get_coordinates(landmarks, mp_pose, 'left', 'elbow')
#         wrist = get_coordinates(landmarks, mp_pose, 'left', 'wrist')
        
#         # calculate elbow angle
#         angle = calculate_angle(shoulder, elbow, wrist)
        
#         # curl counter logic
#         if angle < 30:
#             curl_stage = "up" 
#         if angle > 140 and curl_stage =='up':
#             curl_stage="down"  
#             curl_counter +=1
#         press_stage = None
#         squat_stage = None
#         pushup_stage = None
#         bench_press_stage = None
#         lateral_raises_stage = None
            
#         # Viz joint angle
#         viz_joint_angle(image, angle, elbow)
        
#     elif current_action == "PushUp":
#         # Get coordinates
#         shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
#         elbow = get_coordinates(landmarks, mp_pose, 'left', 'elbow')
#         wrist = get_coordinates(landmarks, mp_pose, 'left', 'wrist')

#         # Calculate elbow angle
#         elbow_angle = calculate_angle(shoulder, elbow, wrist)

#         # PushUp counter logic
#         if elbow_angle < 90:  # Adjust the angle as needed for your specific use case
#             pushup_stage = "down"
#         if elbow_angle > 160 and pushup_stage == "down":
#             pushup_stage = "up"
#             pushup_counter += 1

#         curl_stage = None
#         press_stage = None
#         squat_stage = None
#         bench_press_stage = None
#         lateral_raises_stage = None

#         # Viz joint angle
#         viz_joint_angle(image, elbow_angle, elbow)

#     elif current_action == "Lateral Raises":
#         # Add code for counting "Lateral Raises" repetitions here
#         # Get coordinates
#         shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
#         hip = get_coordinates(landmarks, mp_pose, 'left', 'hip')
#         wrist = get_coordinates(landmarks, mp_pose, 'left', 'wrist')

#         # Calculate elbow angle
#         elbow_angle = calculate_angle(hip, shoulder,wrist)

#         # Lateral Raises counter logic
#         if elbow_angle > 90:  # Adjust the angle as needed for your specific use case
#             lateral_raises_stage = "up"
#         if elbow_angle < 90 and lateral_raises_stage == "up":
#             lateral_raises_stage = "down"
#             lateral_raises_counter += 1

#         curl_stage = None
#         pushup_stage = None
#         press_stage = None
#         squat_stage = None
#         bench_press_stage = None

#         # Viz joint angle
#         viz_joint_angle(image, elbow_angle, elbow)

#     elif current_action == 'Shoulder Press':

#         # Get coords
#         shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
#         elbow = get_coordinates(landmarks, mp_pose, 'left', 'elbow')
#         wrist = get_coordinates(landmarks, mp_pose, 'left', 'wrist')

#         # Calculate elbow angle
#         elbow_angle = calculate_angle(shoulder, elbow, wrist)

#         # Compute distances between joints
#         shoulder2elbow_dist = abs(math.dist(shoulder,elbow))
#         shoulder2wrist_dist = abs(math.dist(shoulder,wrist))

#         # Press counter logic
#         if (elbow_angle > 130) and (shoulder2elbow_dist < shoulder2wrist_dist):
#             press_stage = "up"
#         if (elbow_angle < 50) and (shoulder2elbow_dist > shoulder2wrist_dist) and (press_stage =='up'):
#             press_stage='down'
#             press_counter += 1
#         curl_stage = None
#         squat_stage = None
#         pushup_stage = None
#         bench_press_stage = None
#         lateral_raises_stage = None

#         # Viz joint angle
#         viz_joint_angle(image, elbow_angle, elbow)
        
#     elif current_action == "Bench Press":
#         # Get coordinates
#         shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
#         elbow = get_coordinates(landmarks, mp_pose, 'left', 'elbow')
#         wrist = get_coordinates(landmarks, mp_pose, 'left', 'wrist')

#         # Calculate elbow angle
#         elbow_angle = calculate_angle(shoulder, elbow, wrist)

#         # Bench Press counter logic
#         if elbow_angle > 90:  # Adjust the angle as needed for your specific use case
#             bench_press_stage = "up"
#         if elbow_angle < 45 and bench_press_stage == "up":
#             bench_press_stage = "down"
#             bench_press_counter += 1

#         curl_stage = None
#         pushup_stage = None
#         press_stage = None
#         squat_stage = None
#         lateral_raises_stage = None  # Assuming you don't want to count lateral raises during bench press

#         # Viz joint angle
#         viz_joint_angle(image, elbow_angle, elbow)


#     elif current_action == 'Squat':
#         # Get coords
#         # left side
#         left_shoulder = get_coordinates(landmarks, mp_pose, 'left', 'shoulder')
#         left_hip = get_coordinates(landmarks, mp_pose, 'left', 'hip')
#         left_knee = get_coordinates(landmarks, mp_pose, 'left', 'knee')
#         left_ankle = get_coordinates(landmarks, mp_pose, 'left', 'ankle')
#         # right side
#         right_shoulder = get_coordinates(landmarks, mp_pose, 'right', 'shoulder')
#         right_hip = get_coordinates(landmarks, mp_pose, 'right', 'hip')
#         right_knee = get_coordinates(landmarks, mp_pose, 'right', 'knee')
#         right_ankle = get_coordinates(landmarks, mp_pose, 'right', 'ankle')
        
#         # Calculate knee angles
#         left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
#         right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
        
#         # Calculate hip angles
#         left_hip_angle = calculate_angle(left_shoulder, left_hip, left_knee)
#         right_hip_angle = calculate_angle(right_shoulder, right_hip, right_knee)
        
#         # Squat counter logic
#         thr = 165
#         if (left_knee_angle < thr) and (right_knee_angle < thr) and (left_hip_angle < thr) and (right_hip_angle < thr):
#             squat_stage = "down"
#         if (left_knee_angle > thr) and (right_knee_angle > thr) and (left_hip_angle > thr) and (right_hip_angle > thr) and (squat_stage =='down'):
#             squat_stage='up'
#             squat_counter += 1
            
#         curl_stage = None
#         pushup_stage = None
#         press_stage = None
#         bench_press_stage = None
#         lateral_raises_stage = None
            
#         # Viz joint angles
#         viz_joint_angle(image, left_knee_angle, left_knee)
#         viz_joint_angle(image, left_hip_angle, left_hip)
        
#     else:
#         pass


# # 12. Test in Real Time

# In[17]:


actions = ['Bench Press', 'PushUp', 'Barbell Biceps Curl', 'Shoulder Press', 'Squat']


# In[18]:


def prob_viz(res, actions, input_frame, colors):
    """
    This function displays the model prediction probability distribution over the set of exercise classes
    as a horizontal bar graph
    
    """
    output_frame = input_frame.copy()
    print(res)
    for num, prob in enumerate(res):        
        cv2.rectangle(output_frame, (0,90+num*40), (int(prob*100), 90+num*40), colors[num], -1)
        cv2.putText(output_frame, actions[num], (0, 85+num*40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        
    return output_frame


# In[34]:


# 1. New detection variables
# sequence = []
# predictions = []
# res = []
# threshold = 0.5 # minimum confidence to classify as an action/exercise
# current_action = ''

# # Rep counter logic variables
# curl_counter = 0
# press_counter = 0
# squat_counter = 0
# bench_press_counter = 0
# pushup_counter = 0

# lateral_raises_counter = 0
# curl_stage = None
# press_stage = None
# squat_stage = None
# bench_press_stage = None
# pushup_stage = None
# lateral_raises_stage = None

# # Camera object
# cap = cv2.VideoCapture(0)

# # Video writer object that saves a video of the real time test
# fourcc = cv2.VideoWriter_fourcc('M','J','P','G') # video compression format
# HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) # webcam video frame height
# WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) # webcam video frame width
# FPS = int(cap.get(cv2.CAP_PROP_FPS)) # webcam video fram rate 

# video_name = os.path.join(os.getcwd(),f"{model_name}_real_time_test.avi")
# out = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*"MJPG"), FPS, (WIDTH,HEIGHT))

# # Set mediapipe model 
# with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
#     while cap.isOpened():

#         # Read feed
#         ret, frame = cap.read()
#         print(frame)
#         # break()

#         # Make detection
#         image, results = mediapipe_detection(frame, pose)
        
#         # Draw landmarks
#         draw_landmarks(image, results)
        
#         # 2. Prediction logic
#         keypoints = extract_keypoints(results)        
#         sequence.append(keypoints)      
#         sequence = sequence[-sequence_length:]
              
#         if len(sequence) == sequence_length:
#             res = model.predict(np.expand_dims(sequence, axis=0), verbose=0)[0]  
#             print("workingggggg")
#             predictions.append(np.argmax(res))
#             current_action = actions[np.argmax(res)]
#             confidence = np.max(res)
            
#         #3. Viz logic
#             # Erase current action variable if no probability is above threshold
#             if confidence < threshold:
#                 current_action = ''

#             # Viz probabilities
#             image = prob_viz(res, actions, image, colors)
            
#             # Count reps
#             try:
#                 landmarks = results.pose_landmarks.landmark
#                 count_reps(
#                     image, current_action, landmarks, mp_pose)
#             except:
#                 pass

#             # Display graphical information
#             cv2.rectangle(image, (0,0), (640, 70), colors[np.argmax(res)], -1)
#             cv2.putText(image, 'curl ' + str(curl_counter), (3,30), 
#                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
#             cv2.putText(image, 'press ' + str(press_counter), (240,30), 
#                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
#             cv2.putText(image, 'squat ' + str(squat_counter), (490,30), 
#                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
# #             cv2.putText(image, 'lateral ' + str(lateral_raises_counter), (3,60), 
# #                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
#             cv2.putText(image, 'pushup ' + str(pushup_counter), (240,60), 
#                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
#             cv2.putText(image, 'bench' + str(bench_press_counter), (490,60), 
#                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
         
#         # Show to screen
#         cv2.imshow('OpenCV Feed', image)
        
#         # Write to video file
#         if ret == True:
#             out.write(image)

#         # Break gracefully
#         if cv2.waitKey(10) & 0xFF == ord('q'):
#             break
#     cap.release()
#     out.release()
#     cv2.destroyAllWindows()


# # In[31]:


# print(np.shape(sequence))


# In[33]:


# 1. New detection variables
# sequence = []
# predictions = []
# res = []
# threshold = 0.5 # minimum confidence to classify as an action/exercise
# current_action = ''

# # Rep counter logic variables
# curl_counter = 0
# press_counter = 0
# squat_counter = 0
# curl_stage = None
# press_stage = None
# squat_stage = None

# # Camera object
# cap = cv2.VideoCapture('squats.mp4')

# # Video writer object that saves a video of the real time test
# fourcc = cv2.VideoWriter_fourcc('M','J','P','G') # video compression format
# HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) # webcam video frame height
# WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) # webcam video frame width
# FPS = int(cap.get(cv2.CAP_PROP_FPS)) # webcam video fram rate 

# video_name = os.path.join(os.getcwd(),f"{model_name}_real_time_test.avi")
# out = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*"MJPG"), FPS, (WIDTH,HEIGHT))

# # Set mediapipe model 
# with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
#     while cap.isOpened():

#         # Read feed
#         ret, frame = cap.read()
#         print(frame)

#         # Make detection
#         image, results = mediapipe_detection(frame, pose)
        
#         # Draw landmarks
#         draw_landmarks(image, results)
        
#         # 2. Prediction logic
#         keypoints = extract_keypoints(results)        
#         sequence.append(keypoints)      
#         sequence = sequence[-sequence_length:]
              
#         if len(sequence) == sequence_length:
#             res = model.predict(np.expand_dims(sequence, axis=0), verbose=0)[0]           
#             predictions.append(np.argmax(res))
#             current_action = actions[np.argmax(res)]
#             confidence = np.max(res)
            
#         #3. Viz logic
#             # Erase current action variable if no probability is above threshold
#             if confidence < threshold:
#                 current_action = ''

#             # Viz probabilities
#             image = prob_viz(res, actions, image, colors)
            
#             # Count reps
#             try:
#                 landmarks = results.pose_landmarks.landmark
#                 count_reps(
#                     image, current_action, landmarks, mp_pose)
#             except:
#                 pass

#             # Display graphical information
#             cv2.rectangle(image, (0,0), (640, 40), colors[np.argmax(res)], -1)
#             cv2.putText(image, 'curl ' + str(curl_counter), (3,30), 
#                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
#             cv2.putText(image, 'press ' + str(press_counter), (240,30), 
#                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
#             cv2.putText(image, 'squat ' + str(squat_counter), (490,30), 
#                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
         
#         # Show to screen
#         cv2.imshow('OpenCV Feed', image)
        
#         # Write to video file
#         if ret == True:
#             out.write(image)

#         # Break gracefully
#         if cv2.waitKey(10) & 0xFF == ord('q'):
#             break
#     cap.release()
#     out.release()
#     cv2.destroyAllWindows()


# # In[ ]:


# cap.release()
# out.release()
# cv2.destroyAllWindows()

