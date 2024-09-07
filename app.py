import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from camera import Video
import cv2
import numpy as np
from keras.models import load_model
import time
import traceback
import pandas as pd
from flask import Flask,session, render_template, Response, request, jsonify
import mysql.connector
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random

conn = mysql.connector.connect(host="localhost", user="root", password="@#vthesiya@#778", database="project")
cursor = conn.cursor()


app = Flask(__name__)

facial_expression_processed = False


app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1

@app.route('/')
def start_page():
    return render_template('index.html')

@app.route("/login_signup_page")
def login_signup_page():
    return render_template('login_signup.html')


@app.route("/login",methods=['GET'])
def login():
    try:
        query = "SELECT email, password FROM users;"
        cursor.execute(query)
        result = cursor.fetchall()

        data = [{"Email": row[0], "password": row[1]} for row in result]

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500
    
    
@app.route('/signup',methods=["GET","POST"])
def signup():
    name=request.form.get("name")
    phone=request.form.get("phone")
    email=request.form.get("email")
    password =request.form.get("password")
    
    insert_query = "INSERT INTO users (full_name, phone_no, email, password) VALUES (%s,%s,%s,%s)"
    data_to_insert = (name, phone, email, password)

    cursor.execute(insert_query,data_to_insert)

    conn.commit()
    
    return render_template('login_signup.html')
    
@app.route('/reset_password')
def reset_password():
    return render_template('reset_password.html')

r1=None
l2 = None
@app.route('/recovery',methods=["GET","POST"])
def recovery():
    global r1
    emai_l = request.form.get("email") 
    r1=emai_l
    st="123456789"
    global l2 
    l2= ''
    for i in range(4):
        l2=l2+random.choice(st)

    sender_email = "projectvrdk@gmail.com"
    sender_password = "lvyx lxvz ibfr hhdp"
    recipient_email = emai_l
    subject = "Veryfication Code"
    body = f"verification code : {l2} \n\n **Do not share this code with anyone**"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls() 
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())
    
    # return True
    return render_template('verification.html',emai_l=emai_l)

@app.route('/verify',methods=["GET","POST"])   
def verify():
    data=[l2, r1]
    return jsonify(data)

@app.route('/reset', methods=["GET","POST"])
def reset():
    global r1
    first= request.form.get("password1") 
    second= request.form.get("password2") 

    if first==second:
        q= f"UPDATE users SET password = '{first}' WHERE email= '{r1}'"

        cursor.execute(q)

        conn.commit()
        return render_template('login_signup.html')
    else:
        return render_template('reset_password.html')

    

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/webcam')
def webcam():
    return render_template('webcam.html')

def gen(camera):
    while True:
        frame = camera.get_frame()

        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame +
                   b'\r\n\r\n')
        else:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + b'placeholder_image' +
                   b'\r\n\r\n')


@app.route('/image')
def image():
    return render_template('image.html')

@app.route('/aboutus')
def about():
    return render_template('aboutus.html')


def play_youtube_video(song_info):
    search_query = f"{song_info['Name']} by {song_info['Artist']}"

    browser = webdriver.Chrome()  
    youtube_search_url = f'https://www.youtube.com/results?search_query={search_query}'
    browser.get(youtube_search_url)

    first_video_link = browser.find_element(By.CSS_SELECTOR, 'a#video-title')

    first_video_link.click()

    time.sleep(5)  

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    browser.quit()

global detected_emotion

@app.route('/image', methods=['POST'])
def up_img():
    global facial_expression_processed  
    global detected_emotion

    img = request.files['file']

    img.save('static/file.jpg')

    model = load_model('emotiondetector.h5')
    faceDetect = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    labels_dict = {0:'Angry', 1:'Disgust', 2:'Fear', 3:'Happy', 4:'Neutral', 5:'Sad', 6:'Surprise'}

    frame = cv2.imread("static/file.jpg")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = faceDetect.detectMultiScale(gray, 1.3, 3)

    detected_emotion = None

    for x, y, w, h in faces:
        sub_face_img = gray[y:y+h, x:x+w]
        resized = cv2.resize(sub_face_img, (48, 48))
        normalize = resized / 255.0
        reshaped = np.reshape(normalize, (1, 48, 48, 1))
        result = model.predict(reshaped)
        label = np.argmax(result, axis=1)[0]
        detected_emotion = labels_dict[label]

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 1)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (50, 50, 255), 2)
        cv2.rectangle(frame, (x, y-40), (x+w, y), (50, 50, 255), -1)
        cv2.putText(frame, labels_dict[label], (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imwrite("static/result.jpg", frame)
    filename = "result.jpg"

    facial_expression_processed = True

    return render_template('image.html', filename=filename)


@app.route('/k')
def k():
    global detected_emotion 
    if detected_emotion is not None:
        csv_path = f'{detected_emotion}.csv'
        song_data = pd.read_csv(csv_path)
        if not song_data.empty:
            song_info = song_data.iloc[0].to_dict()
            play_youtube_video(song_info)
    

@app.route('/video')

def video():
    return Response(gen(Video()),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/how_to_use')
def how_to_use():
    return render_template('how_to_use.html')

@app.route('/image1')
def image1():
    return render_template('image.html')

if __name__ == '__main__':
    app.run(debug=True)