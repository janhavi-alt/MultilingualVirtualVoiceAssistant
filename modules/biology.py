import os
import json
import io
import pyttsx3
import pygame
import difflib
import csv
from datetime import datetime
import pytz
from flask import Flask, render_template, jsonify, session, request, redirect, url_for, make_response, send_file
import speech_recognition as sr
from langdetect import detect
from gtts import gTTS
from flask_sqlalchemy import SQLAlchemy
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.units import mm

app = Flask(__name__)
app.secret_key = 'your_secret_key'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "biology_chats.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    user_query = db.Column(db.String(300), nullable=False)
    answer = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))

with app.app_context():
    db.create_all()

engine = pyttsx3.init()
engine.setProperty('rate', 150)

def set_voice(language):
    if language == "en":
        engine.setProperty('voice', 'english')

def speak(text, language="en"):
    if language == "en":
        set_voice(language)
        if engine._inLoop:
            engine.endLoop()
        engine.say(text)
        engine.runAndWait()
    else:
        tts = gTTS(text=text, lang=language)
        audio_data = io.BytesIO()
        tts.write_to_fp(audio_data)
        audio_data.seek(0)

        pygame.mixer.init()
        pygame.mixer.music.stop()
        pygame.mixer.music.load(audio_data)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue

def load_science_questions():
    path = os.path.join(os.path.dirname(__file__), "static", "biology.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def normalize_text(text):
    return text.lower().strip()

science_questions = load_science_questions()

def takeCommandHindiEnglishMarathi():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=7)
            query = r.recognize_google(audio, language='hi-IN,en-IN,mr-IN')
            return query
        except:
            return "None"

def detect_language(text):
    try:
        return detect(text)
    except:
        return "en"

def get_answer_to_question(query):
    normalized_query = normalize_text(query)
    questions = [normalize_text(item['question']) for item in science_questions]
    closest = difflib.get_close_matches(normalized_query, questions, n=1, cutoff=0.6)
    if closest:
        for item in science_questions:
            if normalize_text(item['question']) == closest[0]:
                return item['answer']
    return "माफ करा, या प्रश्नाचं उत्तर माझ्याकडे नाही."

@app.route("/")
def index():
    username = request.args.get('username')
    if username:
        session['username'] = username
    return render_template("biology.html")

@app.route("/process_speech", methods=["POST"])
def process_speech():
    query = takeCommandHindiEnglishMarathi()
    answer = "माफ करा, आवाज ऐकू आला नाही."
    if query != "None":
        language = detect_language(query)
        answer = get_answer_to_question(query)
        speak(answer, language)
        username = session.get('username', 'guest')
        new_chat = ChatHistory(username=username, user_query=query, answer=answer)
        db.session.add(new_chat)
        db.session.commit()
    return jsonify({"message": answer})

@app.route("/biology/history")
def view_chat_history():
    username = session.get('username', 'guest')
    chats = ChatHistory.query.filter_by(username=username).order_by(ChatHistory.timestamp.desc()).all()
    return render_template("chathistory.html", chats=chats)

@app.route("/biology/clear_history", methods=["POST"])
def clear_history():
    username = session.get('username', 'guest')
    ChatHistory.query.filter_by(username=username).delete()
    db.session.commit()
    return redirect(url_for('view_chat_history'))

@app.route("/biology/download/csv")
def download_csv():
    username = session.get('username', 'guest')
    chats = ChatHistory.query.filter_by(username=username).all()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Username', 'User Query', 'Assistant Answer', 'Timestamp'])
    for chat in chats:
        cw.writerow([chat.username, chat.user_query, chat.answer, chat.timestamp.strftime('%d-%m-%Y %I:%M %p')])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=chat_history.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route("/biology/download/pdf")
def download_pdf():
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))

    username = session.get('username', 'guest')
    chats = ChatHistory.query.filter_by(username=username).all()

    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    c.setFont("HeiseiMin-W3", 12)

    y = height - 30
    c.drawCentredString(width / 2, y, f"{username}'s Biology Chat History")
    y -= 20

    for chat in chats:
        block = f"User: {chat.user_query}\nAssistant: {chat.answer}\nTime: {chat.timestamp.strftime('%d-%m-%Y %I:%M %p')}\n---"
        for line in block.splitlines():
            c.drawString(20 * mm, y, line)
            y -= 12
            if y < 30:
                c.showPage()
                c.setFont("HeiseiMin-W3", 12)
                y = height - 30

    c.save()
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="chat_history.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=True)
