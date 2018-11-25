import numpy as np
import cv2
import math

# Camera calibration parameters (centimeters)
#
#     _______________O camera
#     |              |
#     |    ROBOT     |height               image plane
#     |______________|                       /
#       O         O   <------- ground ----->/
#                                          /

camera_height = 12 # height of camera above floor
camera_ground = 60 # distance from point on floor below camera to center of image plane
corridor_width = 30 # width of corridor (or a ruler placed across center of image)
corridor_width_pixels = 580 # pixel width of corridor (or ruler)

def distanceToPixels(distance): # cm to pixel on midline of image
    return int(distance * corridor_width_pixels / corridor_width)

# compute ground distance in pixels for drawing steering arrow
# (this is only correct if camera pointing down at 45 degrees but it will do for illustration)
ground_pixels = distanceToPixels(camera_ground)

def pixelsToDistance(pixels): # pixel to cm on midline of image
    return pixels * corridor_width / corridor_width_pixels

def getSteeringAngle(pixels):
    error = pixelsToDistance(pixels)
    theta = math.atan2(error, camera_ground)
    return math.degrees(theta)


corridorWidth = 0
lastWallLeft = 0
lastWallRight = 0

def steer(lines, width, height):
    global corridorWidth
    global lastWallLeft
    global lastWallRight

    image = np.zeros((height,width,3), np.uint8) # blank (all black) colour image
    if lines is None:
        return image
    left_lines = []
    right_lines = []
    # compute centre pixel
    midX = int(width/2)
    midY = int(height/2)

    for line in lines:
        x1,y1,x2,y2 = line[0]
        cat = category(x1,y1,x2,y2, midX, midY)
        if cat == 'h':
            col = (0,255,255) # yellow
        elif cat == 'r':
            col = (0,255,0) # green
            right_lines.append(normal(sortByY(line[0]))) # sorts by y not x and normalises (averages)
        elif cat == 'l':
            col = (0,0,255) # red
            left_lines.append(normal(sortByY(line[0])))
        elif cat == 'v':
            col = (255,0,0) # blue
        else:
            print("failed to categorise line segment")
            col = (255,0,255) # colour indicates category error

        cv2.line(image,(x1,y1),(x2,y2),col,1)

    steerX = 0
    steerY = 0

    if len(left_lines) > 0:
        sx, sy, leftH, wallLeft = wall_bottom(image, left_lines, midX, midY)
        steerX += sx
        steerY += sy
        lastWallLeft = wallLeft
    else:
        leftH = 0
        wallLeft = lastWallLeft

    if len(right_lines) > 0:
        sx, sy, rightH, wallRight = wall_bottom(image, right_lines, midX, midY)
        steerX += sx
        steerY += sy
        lastWallRight = wallRight
    else:
        rightH = 0
        wallRight = lastWallRight


    # compute midpoint of corridor (wall base blobs)
    middle = int((wallLeft + wallRight) /2) # just x coords

    cv2.arrowedLine (image,(midX, midY+ground_pixels),(middle, midY),(255,255,255),2,cv2.FILLED, 0, 0.02)


    # convert steering correction to variable to use for steering
    steering_correction = round(getSteeringAngle(middle - midX),1)

    corrpx = wallRight - wallLeft
    if corridorWidth > 0:
        corridorWidth = (corrpx + corridorWidth) / 2
    else:
        corridorWidth = corrpx

    #print("pixel width", corridorWidth)

    return image, steering_correction

def wall_bottom(image, lines, midX, midY):
    meanX, meanY, mx, my = mean(lines)
    #vx = mx + 50 # visual offset
    #cv2.line(image,(vx,my),(vx + meanX*2, my + meanY*2),(0,0,255),4)
    hypot = math.hypot(meanX, meanY)
    steerX = meanX / hypot
    steerY = meanY / hypot

    slope = meanY / meanX
    intercept = my - slope * mx
    wallX = int((midY - intercept) / slope)

    point = (wallX, midY)
    # draw blob where horizontal midline intercepts wall base
    cv2.circle(image,point, 10, (255,0,255), -1)
    return steerX, steerY, hypot, wallX


# vars for category()
min_slope = 0.5 # math.atan2(1,2) * 180 / math.pi about 26.6 degrees
max_slope = 6.3

# decide if line segment is left, right or horizontal
# left = 'l', right = 'r', horizontal = 'h' vertical = 'v'
# TODO may need to check y position of lines too
def category(x1,y1,x2,y2, midX, midY):
	xDist = x2 - x1
	if xDist == 0:
	    return 'v'
	slope = abs( (y2 - y1) / xDist )
	if slope < min_slope:
	    return 'h'
	elif slope > max_slope:
	    return 'v'
	left = midX - min(x1, x2)
	right = max(x1, x2) - midX
	if right > left:
	    return 'r'
	else:
	    return 'l'

def degrees(line): # not use - converts slope
    x1,y1,x2,y2 = line
    angle = math.atan2(y2-y1, x2-x1)
    #return round(angle * 180 / math.pi)
    return round(math.degrees(angle))

def sortByY(line):
    x1,y1,x2,y2 = line
    if y1 < y2:
        return line
    else:
        return x2,y2,x1,y1

#def normal(line):
#    x1,y1,x2,y2 = line
#    return x2 - x1, y2 - y1

# return line as vector + centre offset
def normal(line):
    x1,y1,x2,y2 = line
    return x2 - x1, y2 - y1, (x1 + x2)/2, (y1 + y2)/2

def mean(lines):
    sx1=0
    sy1=0
    sx2=0
    sy2=0
    l = len(lines)
    for line in lines:
        x1,y1,x2,y2 = line
        sx1 += x1
        sy1 += y1
        sx2 += x2
        sy2 += y2
    return int(sx1/l), int(sy1/l), int(sx2/l), int(sy2/l)
