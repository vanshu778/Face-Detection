import cv2
import csv
import numpy as np
from keras.models import load_model
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import random

model = load_model('emotiondetector.h5')

labels_dict = {0: 'Angry', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 4: 'Neutral', 5: 'Sad', 6: 'Surprise'}



class Video(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        self.face_detected = False
        self.start_time = None
        self.browser = None  
        self.song_queue = []
        self.ad_skipped = False

    def __del__(self):
        self.video.release()
        if self.browser:
            self.browser.quit()

    def initialize_browser(self):
        self.browser = webdriver.Chrome()  
        self.browser.get("https://www.youtube.com/")

    def find_csv_for_label(self, emotion_label):
        csv_files = {
            'Angry': 'angry.csv',
            'Disgust': 'disgust.csv',
            'Fear': 'fear.csv',
            'Happy': 'happy.csv',
            'Neutral': 'neutral.csv',
            'Sad': 'sad.csv',
            'Surprise': 'surprise.csv'
        }
        return csv_files.get(emotion_label, None)

    def read_names_from_csv(self, csv_filename):
        names = []
        with open(csv_filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'Name' in row and 'Artist' in row:
                    names.append({'Name': row['Name'], 'Artist': row['Artist']})
        return names

    def suggest_song(self, emotion_label, song_data):
        if song_data:
            random.shuffle(song_data)
            
            first_song = song_data[0]
            search_query = f"{first_song['Name']} by {first_song['Artist']}"
            search_url = f'https://www.youtube.com/results?search_query={search_query}'
            self.browser.get(search_url)
            time.sleep(5)  

            first_video = self.browser.find_element("id", "video-title")
            first_video.click()

            time.sleep(5)

            self.song_queue.extend(song_data[1:])
            return f"Suggested songs for {emotion_label} based on song names."
        else:
            return "No song names found for the detected emotion."

    def get_frame(self):
        if not self.face_detected:
            ret, frame = self.video.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 3)

            for x, y, w, h in faces:
                sub_face_img = gray[y:y+h, x:x+w]
                resized = cv2.resize(sub_face_img, (48, 48))
                normalize = resized / 255.0
                reshaped = np.reshape(normalize, (1, 48, 48, 1))
                result = model.predict(reshaped)
                label = np.argmax(result, axis=1)[0]
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 1)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (50, 50, 255), 2)
                cv2.rectangle(frame, (x, y-40), (x+w, y), (50, 50, 255), -1)
                cv2.putText(frame, labels_dict[label], (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                if self.start_time is None:
                    self.start_time = time.time()
                elif time.time() - self.start_time >= 10:
                    self.face_detected = True
                    self.video.release()
                    self.initialize_browser()  

                    csv_filename = self.find_csv_for_label(labels_dict[label])
                    if csv_filename:
                        song_data = self.read_names_from_csv(csv_filename)
                        self.suggest_song(labels_dict[label], song_data)

            ret, jpg = cv2.imencode('.jpg', frame)
            return jpg.tobytes()
        else:
            return None

if __name__ == "__main__":
    video = Video()

    while True:
        frame = video.get_frame()

        if frame is not None:
            cv2.imshow('Webcam Emotion Detection', cv2.imdecode(np.frombuffer(frame, dtype=np.uint8), -1))

        key = cv2.waitKey(1)
        if key == 27:  
            break

    cv2.destroyAllWindows()
