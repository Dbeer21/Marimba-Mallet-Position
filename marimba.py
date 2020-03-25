import librosa
import cv2
import os
import notes
import houghp
import mallet

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
i = 0
frames = []
while cap.isOpened():
    ret, frame = cap.read()
    if ret == False:
        break
    if i == 0:
        base_image = cv2.resize(cv2.flip(frame, -1), (480, 360))
    for notes_frame in struck_notes:
        if i == notes_frame:
            frames.append(cv2.resize(cv2.flip(frame, -1), (480, 360))) 
            break
    i += 1
cap.release()

#print(struck_notes)

note_boundaries = houghp.get_boundaries(base_image) # Get the corners of every marimba bar

#print (note_boundaries)

i = 0
for s in struck_notes:
    crops = []
    bars = []

    for note in struck_notes[s]:
        if note in note_boundaries:
            bars.append(note_boundaries[note])

    for bar in bars:
        min_x, min_y, max_x, max_y = circumscribe(bar) # Circumscribe a 90-degree rectangle with edges parallel to the image
        crop = frames[i][min_y:max_y, min_x:max_x]

        crop_y, crop_x = mallet.find_center(crop)
        if crop_y == -1:
            continue
        else:
            mallet_y = crop_y + min_y
            mallet_x = crop_x + min_x

            cv2.circle(frames[i], (mallet_x,mallet_y), 6, (0,255,0), 2)

        cv2.imshow('frame', frames[i])
        cv2.imshow('crop', crop)

        cv2.waitKey(0)
        cv2.destroyAllWindows()

    i += 1