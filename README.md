# Robotic_Vision
A repository to store programs associated with robotic vision using python and opencv.

The code has been written for a raspberry Pi combined with a PiBorg MonsterBorg Chassis. 
The motor driver in the chassis is a ThunderBorg. 

The following three programs were developed to work together:

maze_edge_detect.py - used for edge detection 

maze_steering.py - an attempt at steering using opncv to see and avoid obstacles.

maze_image_processing - is the main file that calls the other two files and contains the driving element.

The scripts are not yet working as there is a bug that I am currently working on.

The fourth file is:
face_recognition.py - a simple script that detetcs faces in live video, made by following this guide:
https://www.datacamp.com/tutorial/face-detection-python-opencv

