# import the necessary packages
import numpy as np
import cv2

# import imutils

# build a lookup table mapping the pixel values [0, 255] to
# their adjusted gamma values
invGamma = 1.0 / 2.2  # 2.2 is typical gamma for cameras
gammaLUT = np.array([((i / 255.0) ** invGamma) * 255
                     for i in np.arange(0, 256)]).astype("uint8")


def adjust_gamma(image):
    # apply gamma correction using the lookup table
    return cv2.LUT(image, gammaLUT)


# blur = cv2.GaussianBlur(img,(3,3),0)
# median = cv2.medianBlur(img,5)
# blur = cv2.bilateralFilter(img,9,75,75)

def edge(img, doGamma):
    # img = imutils.resize(img, width=640)
    if doGamma:
        img = adjust_gamma(img)
    blur = cv2.GaussianBlur(img, (3, 3), 0)
    # blur = cv2.medianBlur(img,9)
    # blur = cv2.bilateralFilter(img,9,75,75)
    # cv2.imshow("BLUR", blur)
    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
    # cv2.imshow("gray", gray)

    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

    abs_sobelx = np.uint8(np.absolute(sobelx))
    # cv2.imshow("abs_sobelx", abs_sobelx)
    abs_sobely = np.uint8(np.absolute(sobely))

    abs_sobelx = cv2.convertScaleAbs(sobelx)
    abs_sobely = cv2.convertScaleAbs(sobely)

    scaled_sobel = cv2.addWeighted(abs_sobelx, 0.5, abs_sobely, 0.5, 0);
    # Make all pixels over brightness threshold white
    thresh = 20
    _, edged = cv2.threshold(scaled_sobel, thresh, 255, cv2.THRESH_BINARY)

    # cv2.imshow("sobel", edged)

    return edged


def canny(img, doGamma):
    # img = imutils.resize(img, width=640)
    if doGamma:
        img = adjust_gamma(img)
    blur = cv2.GaussianBlur(img, (3, 3), 0)
    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
    edged = cv2.Canny(img, 50, 150, apertureSize=3)

    return edged
