import librosa
import cv2
import os
import notes
import houghp
import mallet

def check_position(mx, my, coords):
    (bx1, by1), (bx2, by2), (tx1, ty1), (tx2, ty2) = [coords[i] for i in range(len(coords))]
    bm = (by2-by1)/(bx2-bx1)
    tm = (ty2-ty1)/(tx2-tx1)

    by = int(by1 + bm * (mx - bx1))
    ty = int(ty1 + tm * (mx - tx1))

    return (by, ty)

def circumscribe(coords):
    min_x = coords[0][0]
    min_y = coords[0][1]
    max_x = coords[0][0]
    max_y = coords[0][1]
    for coord in coords:
        if coord[0] < min_x:
            min_x = coord[0]
        if coord[0] > max_x:
            max_x = coord[0]
        if coord[1] < min_y:
            min_y = coord[1]
        if coord[1] > max_y:
            max_y = coord[1]
    
    return ([min_x - 5, min_y - 5, max_x + 5, max_y + 5])

path = os.path.realpath(__file__).strip('marimba.py')
path = path.replace('\\', "/")
vid_path = path + 'Source/random.mov'

struck_notes = notes.get_notes(vid_path) # Get the timestamps of each struck note

cap = cv2.VideoCapture(vid_path)

# Get all the frames in which a note was struck
i = j = 0
frames = []
while cap.isOpened():
    ret, frame = cap.read()
    if ret == False:
        break
    if i == 0:
        base_image = cv2.resize(cv2.flip(frame, -1), (480, 360))
    for notes_frame in struck_notes:
        if i == notes_frame:
            frames.append({})
            frames[j]['frame'] = cv2.resize(cv2.flip(frame, -1), (480, 360))
            frames[j]['timestamp'] = (i + 3) / 30
            j += 1
            break
    i += 1
cap.release()

#print(struck_notes)

note_boundaries = houghp.get_boundaries(base_image) # Get the corners of every marimba bar

#print (note_boundaries)

i = j = 0
rope_strikes = []
for s in struck_notes: # Each frame with at least one struck note
    crops = []
    bars = []

    for note in struck_notes[s]: # Each note in the frame
        if note in note_boundaries:
            bars.append(note_boundaries[note])

    for bar in bars:
        min_x, min_y, max_x, max_y = circumscribe(bar['bar']) # Circumscribe a 90-degree rectangle with edges parallel to the image
        crop = frames[i]['frame'][min_y:max_y, min_x:max_x]

        crop_x, crop_y = mallet.find_center(crop)
        if crop_x == -1:
            continue
        else:
            mallet_x = crop_x + min_x
            mallet_y = crop_y + min_y

            cv2.circle(frames[i]['frame'], (mallet_x,mallet_y), 6, (0,255,0), 2)

        by, ty = check_position(mallet_x, mallet_y, bar['rope'])
        #cv2.line(frames[i]['frame'], (mallet_x,ty), (mallet_x,by), (255,0,255), 2)
        #cv2.line(frames[i]['frame'], bar['rope'][0], bar['rope'][1], (255,255,255), 2)
        #cv2.line(frames[i]['frame'], bar['rope'][2], bar['rope'][3], (255,255,255), 2)
        #cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
        #cv2.imshow('frame', frames[i]['frame'])
        #cv2.waitKey(0)

        # Struck on rope
        if abs(mallet_y - by) < 10 or abs(mallet_y - ty) < 10:
            rope_strikes.append({})
            rope_strikes[j]['img'] = frames[i]['frame']
            rope_strikes[j]['timestamp'] = round(frames[i]['timestamp'], 2)
            rope_strikes[j]['note'] = list(note_boundaries.keys())[list(note_boundaries.values()).index(bar)]
            j += 1
    i += 1

for strike in rope_strikes:
    strike['img'] = cv2.putText(strike['img'], 'Timestamp: ' + str(strike['timestamp']) + ' seconds', (20,340), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1, cv2.LINE_AA)
    strike['img'] = cv2.putText(strike['img'], 'Note: ' + str(strike['note']), (380,340), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1, cv2.LINE_AA)
    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    cv2.imshow('image', strike['img'])
    cv2.waitKey(0)