# maze_video_main.py
# 25/11/2018

# Bugs and Errors
# Working but when viewing too many lines throws the following errors
#  File "maze_image_processing.py", line 137, in <module>
#    overlay, steering_correction = steer(lines, width, height)
# ValueError: too many values to unpack
# Also get an occasional Divisor by 0 error
# probably need some error checking if not zero?


# import the neccessary packages

from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import cv2
from time import sleep
import math
import os
import sys
import pygame
import ThunderBorg

from maze_edge_detect import edge, canny
from maze_steering import steer

# Re-direct our output to standard error, we need to ignore standard out to hide some nasty print statements from pygame
sys.stdout = sys.stderr

# Setup the ThunderBorg
TB = ThunderBorg.ThunderBorg()
#TB.i2cAddress = 0x15                  # Uncomment and change the value if you have changed the board address
TB.Init()
if not TB.foundChip:
    boards = ThunderBorg.ScanForThunderBorg()
    if len(boards) == 0:
        print("No ThunderBorg found, check you are attached :)")
    else:
        print("No ThunderBorg at address %02X, but we did find boards:" % (TB.i2cAddress))
        for board in boards:
            print("    %02X (%d) " % (board, board))
        print("If you need to change the I2C address change the setup line so it is correct, e.g.")
        print("TB.i2cAddress = 0x%02X" % (boards[0]))
    sys.exit()
# Ensure the communications failsafe has been enabled!
failsafe = False
for i in range(5):
    TB.SetCommsFailsafe(True)
    failsafe = TB.GetCommsFailsafe()
    if failsafe:
        break
if not failsafe:
    print("Board %02X failed to report in failsafe mode!" % (TB.i2cAddress))
    sys.exit()

# Power settings
voltageIn = 1.48 * 10                    # Total battery voltage to the ThunderBorg
voltageOut = 14.8 * 0.95                # Maximum motor voltage, we limit it to 95% to allow the RPi to get uninterrupted power

# Setup the power limits
if voltageOut > voltageIn:
    maxPower = 0.5
else:
    maxPower = voltageOut / float(voltageIn)

# Show battery monitoring settings
battMin, battMax = TB.GetBatteryMonitoringLimits()
battCurrent = TB.GetBatteryReading()
print("Battery monitoring settings:")
print("    Minimum  (red)     %02.2f V" % (battMin))
print("    Half-way (yellow)  %02.2f V" % ((battMin + battMax) / 2))
print("    Maximum  (green)   %02.2f V" % (battMax))
print("")
print("    Current voltage    %02.2f V" % (battCurrent))
print("")

# Setup pygame and wait for the joystick to become available
TB.MotorsOff()
TB.SetLedShowBattery(False)
TB.SetLeds(0,0,1)
os.environ["SDL_VIDEODRIVER"] = "dummy" # Removes the need to have a GUI window
pygame.init()

# Some variables
interval = 0.00                         # Time between updates in seconds, smaller responds faster but uses more processor time

# setup camera
camera = PiCamera()
camera.rotation = 180
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640,480))

# warmup camera
sleep(0.1)

# define image properties (height, width, fps)
height = 480
width = 640
fps = 32

print("We got to here!!!!!!!!")
last_frame = np.zeros((height,width,3), np.uint8) #Does motion blurring
#last_frame.fill(127)

while True:
    TB.SetLedShowBattery(True)
    ledBatteryMode = True

    try:
        print("Press CTRL+C to quit")
        # driveLeft = 0.0 # 25/11/18 moved into camera and driving loop
        # driveRight = 0.0 # 25/11/18 moved into camera and driving loop
        running = True
        # Loop indefinitely
        while running:
        # start the capture
            for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
                frame = frame.array
                #print(frame.shape)
                #height, width, channels = frame.shape
                
                #print("height = ", height)
                #print("width = ", width)

                #last_frame = np.zeros((height, width, 3), np.uint8)

                # motion blurring
                img = cv2.addWeighted(frame, 0.5, last_frame, 0.5, 0);  # takes average of two images
                last_frame = img

                #edged = edge(img, True)  # sobel edge detection, True adds gamma correction
                edged = canny(img, True)  # canny edge detection, True adds gamma correction
                # change edged to canny to use canny detection

                # Apply Probablistic Hough Transform to extract line segments representing edges
                lines = cv2.HoughLinesP(edged, 20, np.pi / 180, 30, minLineLength=70, maxLineGap=20)

                # generate overlay image with processed edges
                overlay, steering_correction = steer(lines, width, height)
                #_, steering_correction = steer(lines, width, height)
                #_, overlay = steer(lines, width, height)
                #print("Hello Sailor Land Ahoy:", steering_correction)
        
                # show the frame with overlay (dims and merges)
                img = cv2.addWeighted(frame, 0.4, overlay, 0.6, 0);
                cv2.imshow("Frame", img)
                #sleep(0.02) # 24/11/18 13:59 added delay to debug ValueError too many values to unpack    
                
                key = cv2.waitKey(1) & 0xFF

                # clear the video stream
                rawCapture.truncate(0)
                
                # quit using the ESC key
                if key == 27:
                    cv2.destroyAllWindows()
                    break
                
                # driving code
                driveLeft = 0.0
                driveRight = 0.0    
                if steering_correction < 0:
                    print("Turning Left")
                    # Turning left
                    driveLeft = 0.0
                    driveRight = 1.0 
                elif steering_correction > 0:
                    # Turning right
                    print("Turining Right")
                    driveLeft = 1.0
                    driveRight = 0.0


                # Custom speed adjustment to slow things down
                driveRight = driveRight * 0.5
                driveLeft = driveLeft * 0.5

                # Set the motors to the new speeds
                TB.SetMotor1(driveRight * maxPower)
                TB.SetMotor2(driveLeft * maxPower)
                print("Steering_Correction", steering_correction)
                print("Drive Right", driveRight)
                print("Drive Left", driveLeft)

                # Change LEDs to purple to show motor faults
                if TB.GetDriveFault1() or TB.GetDriveFault2():
                    if ledBatteryMode:
                        TB.SetLedShowBattery(False)
                        TB.SetLeds(1,0,1)
                        ledBatteryMode = False
                else:
                    if not ledBatteryMode:
                        TB.SetLedShowBattery(True)
                        ledBatteryMode = True
                # Wait for the interval period
                sleep(interval)
            # Disable all drives
            TB.MotorsOff()
    except KeyboardInterrupt:
        # CTRL+C exit, disable all drives
        TB.MotorsOff()
        TB.SetCommsFailsafe(False)
        TB.SetLedShowBattery(False)
        TB.SetLeds(0,0,0)
    print



    

    

