import cv2
import numpy as np
import sys
import os
import statistics

def find_center(crop):
    # Mask/Opening of the cropped image
    lower_blue = np.array([130, 50, 50])
    upper_blue = np.array([240, 180, 180])
    mask = cv2.inRange(crop, lower_blue, upper_blue)
    kernel = np.ones((3,3),np.uint8)
    opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Find all the white pixels in the opening of the mask
    white_pixels = [[],[]]
    for i in range(len(opening)):
        for j in range(len(opening[i])):
            if opening[i][j] == 255:
                white_pixels[0].append(j)
                white_pixels[1].append(i)

    if white_pixels[0]: # Mallet present
        med_x = int(statistics.median(white_pixels[0]))
        med_y = int(statistics.median(white_pixels[1]))
    else:  # No mallet present
        med_x = med_y = -1

    return [med_x, med_y]