import librosa
import os
import math
import numpy as np
import moviepy.editor as mp

def get_notes(vid_path, fps):
    aud_path = vid_path[:-3] + 'wav'

    clip = mp.VideoFileClip(vid_path)
    clip.audio.write_audiofile(aud_path)

    #f = open(vid_path[:-4] + '_output.txt', 'w')

    y, sr = librosa.load(aud_path)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    peaks = librosa.util.peak_pick(onset_env, 5, 5, 5, 5, 7, 5)
    sec_peaks = librosa.frames_to_time(peaks, sr=sr)
    #print(peaks)

    timestamps = {}
    for peak in sec_peaks:
        yp, srp = librosa.load(aud_path, offset=peak, duration=0.2)
        pitches, magnitudes = librosa.piptrack(y=yp, sr=srp)

        #f.write('Timestamp: ')
        #f.write(str(peak))
        #f.write(' seconds')
        #f.write('\n')

        # Grab the pitches and magnitudes from the cluttered arrays
        real_pitches = []
        real_magnitudes = []
        for i in range(len(pitches)):
            for j in range(len(pitches[i])):
                if pitches[i][j] > 107 and pitches[i][j] < 2140: #A2-C7
                    real_pitches.append(pitches[i][j])
                    real_magnitudes.append(magnitudes[i][j])

                    #f.write(str(pitches[i][j]))
                    #f.write(' = ')
                    #f.write(librosa.hz_to_note(pitches[i][j]))
                    #f.write(' with a volume of: ')
                    #f.write(str(magnitudes[i][j]))
                    #f.write(' and a tuning of: ')
                    #f.write(str(librosa.core.pitch_tuning(pitches[i][j], resolution=0.001)))
                    #f.write('\n')
        
        # Put the pitches/magnitudes into a dictionary {'note': [magnitudes]}
        note_dict = {}
        for i in range(len(real_pitches)):
            if abs(librosa.core.pitch_tuning(real_pitches[i], resolution=0.001)) < 0.2:
                temp_pitch = librosa.hz_to_note(real_pitches[i])
                if temp_pitch not in note_dict:
                    note_dict[temp_pitch] = []
                note_dict[temp_pitch].append(real_magnitudes[i])

        # Get the average magnitude of all the frequencies in the peak
        total_mag_sum = 0
        total_mag_count = 0
        for real_magnitude in real_magnitudes:
            total_mag_sum += real_magnitude
            total_mag_count += 1
        
        # Determine the magnitude threshold
        mag_threshold = total_mag_sum / total_mag_count
        if mag_threshold > 20:
            mag_threshold = 20
        elif mag_threshold < 2:
            mag_threshold = 2

        #f.write('Magnitude Average: ')
        #f.write(str(total_mag_sum / total_mag_count))
        #f.write('\n')
        #f.write("Magnitude Threshold: ")
        #f.write(str(mag_threshold))
        #f.write('\n')

        # Get the average frequency count of all the notes in the peak and determine the frequency count threshold
        note_count = len(note_dict)
        freq_count = 0
        for x in note_dict:
            freq_count += len(note_dict[x])
        freq_count_threshold = math.floor(freq_count / note_count)

        #f.write('Frequency Count Average: ')
        #f.write(str(freq_count / note_count))
        #f.write('\n')
        #f.write("Frequency Count Threshold: ")
        #f.write(str(freq_count_threshold))
        #f.write('\nSTRUCK NOTES:\n')

        for x in note_dict:
            if (len(note_dict[x]) < freq_count_threshold):
                continue
            mag_sum = 0
            mag_count = 0
            for y in note_dict[x]:
                mag_sum += y
                mag_count += 1
            mag_avg = mag_sum / mag_count

            if (mag_avg > mag_threshold):
                frame = round(peak * fps) - 1 # Convert timestamp to frame number
                if frame not in timestamps:
                    timestamps[frame] = []
                timestamps[frame].append(x)
                #f.write(str(librosa.note_to_hz(x)))
                #f.write(' = ')
                #f.write(x)
                #f.write(' at a volume of: ')
                #f.write(str(mag_avg))
                #f.write('\n')

        #f.write('\n')
    #f.close()
    
    os.remove(aud_path)
    return (timestamps)
        
