import cv2
import numpy as np

def mask(frame):
    img = cv2.resize(frame, (480, 360), interpolation = cv2.INTER_AREA)

    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    hls = cv2.cvtColor(img, cv2.COLOR_RGB2HLS)

    lower_brown = np.array([24, 55, 80])
    upper_brown = np.array([255, 255, 255])
    lower_brown_rgb = np.array([140, 120, 100])
    lower_gray = np.array([140, 130, 120])
    upper_gray = np.array([200, 200, 200])
    lower_blue = np.array([200, 180, 160])
    upper_blue = np.array([210, 200, 200])

    hsv_mask = cv2.inRange(hsv, lower_brown, upper_brown)
    hls_mask = cv2.inRange(hls, lower_brown, upper_brown)
    rgb_mask = cv2.inRange(img, lower_brown_rgb, upper_brown)
    gray_mask = cv2.inRange(img, lower_gray, upper_gray)
    blue_mask = cv2.inRange(img, lower_blue, upper_blue)
    mask = hsv_mask + hls_mask + rgb_mask - gray_mask - blue_mask

    result = cv2.bitwise_and(img, img, mask=mask)

    kernel = np.ones((8,8),np.uint8)
    opening = cv2.morphologyEx(result, cv2.MORPH_OPEN, kernel)

    return (opening)