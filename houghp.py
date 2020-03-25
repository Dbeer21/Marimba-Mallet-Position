import librosa
import cv2
import os
import numpy as np
import math
import mask_color

def average_lines(lines):
    sum_x1 = sum_y1 = sum_x2 = sum_y2 = 0
    for x1, y1, x2, y2 in lines:
        sum_x1 += x1
        sum_y1 += y1
        sum_x2 += x2
        sum_y2 += y2
        
    return ([int(sum_x1/len(lines)), int(sum_y1/len(lines)), int(sum_x2/len(lines)), int(sum_y2/len(lines))])

def interpolate_hori(line):
    x1 = line[0]
    y1 = line[1]
    x2 = line[2]
    y2 = line[3]
    m = (y2-y1)/(x2-x1)

    return ([0, int(y1 + m * (0 - x1)), 480, int(y1 + m * (480 - x1))])

def interpolate_vert(line, bot_line, top_line):
    # Vertical line
    l_x1 = line[0]
    l_y1 = line[1]
    l_x2 = line[2]
    l_y2 = line[3]
    if l_x1 != l_x2:
        l_m = (l_y2-l_y1)/(l_x2-l_x1)
        l_b = l_m*(-l_x1)+l_y1

    # Bottom line
    b_x1 = bot_line[0]
    b_y1 = bot_line[1]
    b_x2 = bot_line[2]
    b_y2 = bot_line[3]
    if b_x1 != b_x2:
        b_m = (b_y2-b_y1)/(b_x2-b_x1)
        b_b = b_m*(-b_x1)+b_y1

    # Top line
    t_x1 = top_line[0]
    t_y1 = top_line[1]
    t_x2 = top_line[2]
    t_y2 = top_line[3]
    if t_x1 != t_x2:
        t_m = (t_y2-t_y1)/(t_x2-t_x1)
        t_b = t_m*(-t_x1)+t_y1

    # Calculate intersects
    if l_x1 == l_x2:
        x1 = l_x1
        x2 = l_x2
    else:
        x1 = int(((l_b-b_b)/(b_m-l_m)))
        x2 = int((l_b-t_b)/(t_m-l_m))
    y1 = int(b_m*x1+b_b)
    y2 = int(t_m*x1+t_b)

    return ([x1, y1, x2, y2])

def merge_close_lines(lines, spread):
    merged_lines = []
    close_lines = []
    for i in range(len(lines)):
        close_lines.append(lines[i])
        if i < len(lines) - 1:
            if abs(lines[i][0] - lines[i+1][0]) + abs(lines[i][2] - lines[i+1][2]) > spread:
                merged_lines.append(average_lines(close_lines))
                close_lines.clear()
                spread -= 0.1
        else:
            merged_lines.append(average_lines(close_lines))
    
    return (merged_lines)

def get_boundaries(frame):
    #imgPath = os.path.realpath(__file__).strip('houghp.py')
    #imgPath = imgPath.replace('\\', "/")
    #frame = cv2.imread(imgPath + 'Source/marimba_still.png')

    img = mask_color.mask(frame)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray,100,400)

    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 36, None, 5, 60)

    vert_lines = []
    hori_lines = []
    diag_lines = []
    for line in lines:
        x1 = line[0][0]
        y1 = line[0][1]
        x2 = line[0][2]
        y2 = line[0][3]
        angle = math.atan2(abs(y2-y1), abs(x2-x1))
        if abs(angle - np.pi/2) < 5*np.pi/180:
            #cv2.line(img,(x1, y1),(x2, y2),(0,255,0),2)
            if y2 > y1:
                y1, y2 = y2, y1
                x1, x2 = x2, x1
            vert_lines.append([x1,y1,x2,y2])
        elif abs(angle) < 2*np.pi/180:
            #cv2.line(img,(x1, y1),(x2, y2),(0,0,255),2)
            hori_lines.append([x1,y1,x2,y2])
        elif abs(angle) > 2*np.pi/180 and abs(angle) < 15*np.pi/180:
            #cv2.line(img,(x1, y1),(x2, y2),(255,0,0),2)
            diag_lines.append([x1,y1,x2,y2])

    # Get center horizontal line of marimba
    horizontal_line = interpolate_hori(average_lines(hori_lines))
    hori_y = int((horizontal_line[1] + horizontal_line[3]) / 2)
    hori_m = (horizontal_line[1] - horizontal_line[3])/(horizontal_line[2] - horizontal_line[0])

    # Get the top and bottom diagonal lines of marimba
    top_diag_lines = []
    bot_diag_lines = []
    for x1, y1, x2, y2 in diag_lines:
        if y1 > hori_y + 60 and y2 > hori_y + 60:
            bot_diag_lines.append([x1, y1, x2, y2])
        elif y2 < hori_y - 60 and y2 < hori_y - 60:
            top_diag_lines.append([x1, y1, x2, y2])
    top_diag_line = interpolate_hori(average_lines(top_diag_lines))
    bot_diag_line = interpolate_hori(average_lines(bot_diag_lines))

    # Insertion sort of vertical lines
    for i in range(1, len(vert_lines)):
        key = vert_lines[i]
        keyVal = key[0]
        j = i-1
        while j >= 0 and keyVal < vert_lines[j][0]:
            vert_lines[j+1] = vert_lines[j]
            j -= 1
        vert_lines[j+1] = key

    # Split white and black keys
    black_vert_lines = []
    white_vert_lines = []
    for x1, y1, x2, y2 in vert_lines:
        if y1 > hori_y + 30: # lines below
            white_vert_lines.append(interpolate_vert([x1, y1, x2, y2], bot_diag_line, horizontal_line))
        if y2 < hori_y - 30: # lines above
            black_vert_lines.append(interpolate_vert([x1, y1, x2, y2], horizontal_line, top_diag_line))

    # Merge close-by lines for black keys (two trials)
    merged_white_lines = merge_close_lines(white_vert_lines, 13)
    merged_black_lines = merge_close_lines(black_vert_lines, 15)

    # Find corners of keys
    note_boundaries = {}
    freq = 110
    w = b = 0
    while b < len(merged_black_lines) - 1 or w < len(merged_white_lines) - 1:
        key = librosa.core.hz_to_note(freq)
        if key[1] == '#': # accidental
            note_boundaries[key] = [(merged_black_lines[b][0], merged_black_lines[b][1]), (merged_black_lines[b+1][0], merged_black_lines[b+1][1]), (merged_black_lines[b+1][2], merged_black_lines[b+1][3]), (merged_black_lines[b][2], merged_black_lines[b][3])]
            if key[0] == 'A' or key[0] == 'D': # skip gap in black keys
                b += 2
            else:
                b += 1
        else: # natural
            note_boundaries[key] = [(merged_white_lines[w][0], merged_white_lines[w][1]), (merged_white_lines[w+1][0], merged_white_lines[w+1][1]), (merged_white_lines[w+1][2], merged_white_lines[w+1][3]), (merged_white_lines[w][2], merged_white_lines[w][3])]
            w += 1
        freq *= 2**(1/12)

    # Display lines
    #for x1,y1,x2,y2 in merged_white_lines:
    #    cv2.line(img,(x1, y1),(x2, y2),(0,255,0),2)
    #for x1,y1,x2,y2 in merged_black_lines:
    #    cv2.line(img,(x1, y1),(x2, y2),(0,255,255),2)

    # Display note bounding boxes
    #for n in note_boundaries:
    #    r = np.random.randint(256)
    #    g = np.random.randint(256)
    #    b = np.random.randint(256)
    #    for i in range(3):
    #        cv2.line(img, note_boundaries[n][i], note_boundaries[n][i+1], (r, g, b), 2)
    #    cv2.line(img, note_boundaries[n][3], note_boundaries[n][0], (r, g, b), 2)
    #cv2.line(img, (horizontal_line[0], horizontal_line[1]), (horizontal_line[2], horizontal_line[3]), (0, 0, 255), 2)
    #cv2.line(img, (top_diag_line[0], top_diag_line[1]), (top_diag_line[2], top_diag_line[3]), (255, 0, 0), 2)
    #cv2.line(img, (bot_diag_line[0], bot_diag_line[1]), (bot_diag_line[2], bot_diag_line[3]), (255, 255, 0), 2)

    #cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    #cv2.imshow('image', img)

    #k = cv2.waitKey(0)
    #if k == 27:
    #    cv2.destroyAllWindows()
    #elif k == 115:
    #    cv2.imwrite(imgPath + 'Source/houghp.png',img)
    #    cv2.destroyAllWindows()

    return (note_boundaries)