import librosa
import cv2
import os
import tkinter as tk
import notes
import houghp
import mallet
from matplotlib import pyplot as plt
from matplotlib.widgets import Button
from tkinter.filedialog import askopenfilename

class Base(object):
    def __init__(self, images):
        self.ind = 0
        self.loaded = False
        self.flip_h = False
        self.flip_v = False
        self.images = images
        self.setup()

    def next(self, event):
        if self.ind < len(self.images) - 1:
            self.ind += 1
        else:
            self.ind = 0
        self.setup()

    def prev(self, event):
        if self.ind > 0:
            self.ind -= 1
        else:
            self.ind = len(self.images) - 1
        self.setup()

    def select(self, event):
        plt.close()
        self.selection = self.images[self.ind]

    def load(self, event):
        filename = askopenfilename()
        plt.close()
        if cv2.imread(filename).all() != None:
            self.loaded = True
            self.selection = cv2.imread(filename)
        else:
            self.setup(1)

    def fliph(self, event):
        plt.close()
        self.flip_h = not self.flip_h
        self.setup()

    def flipv(self, event):
        plt.close()
        self.flip_v = not self.flip_v
        self.setup()

    def setup(self, err = 0):
        plt.close()
        if self.flip_h and self.flip_v:
            plt.imshow(cv2.cvtColor(cv2.flip(self.images[self.ind], -1), cv2.COLOR_BGR2RGB))
        elif self.flip_h and not self.flip_v:
            plt.imshow(cv2.cvtColor(cv2.flip(self.images[self.ind], 0), cv2.COLOR_BGR2RGB))
        elif not self.flip_h and self.flip_v:
            plt.imshow(cv2.cvtColor(cv2.flip(self.images[self.ind], 1), cv2.COLOR_BGR2RGB))
        else:
            plt.imshow(cv2.cvtColor(self.images[self.ind], cv2.COLOR_BGR2RGB))
        
        if err == 0:
            plt.title('Choose the least interrupted frame of the marimba: ' + str(self.ind + 1))
        else:
            plt.title('Error: Not an image\nChoose the least interrupted frame of the marimba: ' + str(self.ind + 1))
        plt.xticks([]),plt.yticks([])

        # Positions
        axnext = plt.axes([0.4, 0.05, 0.1, 0.075])
        axprev = plt.axes([0.1, 0.05, 0.1, 0.075])
        axsel = plt.axes([0.25, 0.05, 0.1, 0.075])
        axload = plt.axes([0.7, 0.05, 0.2, 0.075])
        axfliph = plt.axes([0.2, 0.2, 0.2, 0.075])
        axflipv = plt.axes([0.6, 0.2, 0.2, 0.075])
        
        # Buttons
        bnext = Button(axnext, 'Next')
        bprev = Button(axprev, 'Previous')
        bsel = Button(axsel, 'Select')
        bload = Button(axload, 'Load from File')
        bfliph = Button(axfliph, 'Flip Horizontal')
        bflipv = Button(axflipv, 'Flip Vertical')

        # Button events
        bnext.on_clicked(self.next)
        bprev.on_clicked(self.prev)
        bsel.on_clicked(self.select)
        bload.on_clicked(self.load)
        bfliph.on_clicked(self.fliph)
        bflipv.on_clicked(self.flipv)

        plt.show()

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

root = tk.Tk()
root.withdraw()
vid_path = askopenfilename()
root.destroy()

cap = cv2.VideoCapture(vid_path)

fps = cap.get(cv2.CAP_PROP_FPS)
video_images = []
bar_frames = []

struck_notes = notes.get_notes(vid_path, fps) # Get the timestamps of each struck note

# Get all the frames in which a note was struck
i = j = 0
base_images = []
hit_frames = []
while cap.isOpened():
    ret, frame = cap.read()
    if ret == False:
        break
    if i < (15 * 10) and i % 15 == 0:
        base_images.append(cv2.resize(frame, (480, 360)))
    video_images.append(cv2.resize(frame, (480, 360)))
    if i in struck_notes:
        hit_frames.append({})
        hit_frames[j]['image'] = cv2.resize(frame, (480, 360))
        hit_frames[j]['frame'] = i
        j += 1
    i += 1
cap.release()

# Let the user decide which frame to use as the base image
callback = Base(base_images)
base_image = callback.selection

# Flip images if user specified
if callback.flip_h or callback.flip_v:
    if callback.flip_h and callback.flip_v:
        flip = -1
    elif callback.flip_h and not callback.flip_v:
        flip = 0
    else:
        flip = 1

    if not callback.loaded:
        base_image = cv2.flip(base_image, flip)
    for i in range(len(video_images)):
        video_images[i] = cv2.flip(video_images[i], flip)
    for i in range(len(hit_frames)):
        hit_frames[i]['image'] = cv2.flip(hit_frames[i]['image'], flip)       

note_boundaries = houghp.get_boundaries(base_image) # Get the corners of every marimba bar

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
        crop = hit_frames[i]['image'][min_y:max_y, min_x:max_x]

        crop_x, crop_y = mallet.find_center(crop)
        if crop_x == -1:
            continue
        else:
            mallet_x = crop_x + min_x
            mallet_y = crop_y + min_y

            cv2.line(hit_frames[i]['image'], (0, 0), (0, 359), (0, 0, 255), 2)
            cv2.line(hit_frames[i]['image'], (0, 359), (479, 359), (0, 0, 255), 2)
            cv2.line(hit_frames[i]['image'], (479, 359), (479, 0), (0, 0, 255), 2)
            cv2.line(hit_frames[i]['image'], (479, 0), (0, 0), (0, 0, 255), 2)

        by, ty = check_position(mallet_x, mallet_y, bar['rope'])
        #cv2.line(hit_frames[i]['image'], (mallet_x,ty), (mallet_x,by), (255,0,255), 2)
        #cv2.line(hit_frames[i]['image'], bar['rope'][0], bar['rope'][1], (255,255,255), 2)
        #cv2.line(hit_frames[i]['image'], bar['rope'][2], bar['rope'][3], (255,255,255), 2)
        #cv2.namedWindow('test', cv2.WINDOW_FULLSCREEN)
        #cv2.imshow('test', hit_frames[i]['image'])
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()

        # Struck on rope
        if abs(mallet_y - by) < 10 or abs(mallet_y - ty) < 10:
            cv2.circle(hit_frames[i]['image'], (mallet_x, mallet_y), 6, (0,255,0), 2)
            rope_strikes.append({})
            rope_strikes[j]['image'] = hit_frames[i]['image']
            rope_strikes[j]['frame'] = hit_frames[i]['frame']
            rope_strikes[j]['note'] = list(note_boundaries.keys())[list(note_boundaries.values()).index(bar)]
            bar_frames.append(rope_strikes[j]['frame'])
            j += 1
    i += 1

# Format frame of misplaced hit
for strike in rope_strikes:
    strike['image'] = cv2.putText(strike['image'], 'Timestamp: ' + str(round((strike['frame'] + (fps / 10)) / fps, 2)) + ' seconds', (20,340), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1, cv2.LINE_AA)
    strike['image'] = cv2.putText(strike['image'], 'Note: ' + str(strike['note']), (380,340), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1, cv2.LINE_AA)
    video_images[strike['frame']] = strike['image']

# Write a video that highlights all the misplaced hits
out = cv2.VideoWriter(vid_path[:-4] + '_output.avi', cv2.VideoWriter_fourcc(*'DIVX'), fps, (480, 360))
for i in range(len(video_images)):
    out.write(video_images[i])
    if i in bar_frames:
        for j in range(round(fps * 3)):
            out.write(video_images[i])
out.release()