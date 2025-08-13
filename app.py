from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import google.generativeai as genai
import os
import speech_recognition as sr
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import re
import json


nltk.download('punkt_tab')

app = Flask(__name__)
app.secret_key = 'my_super_secret_key_456789'

# ===== Configure Gemini API =====
GOOGLE_API_KEY = 'AIzaSyACpD3waeAbKickkjJb7gBHqegPhGGB-VE'
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

EXCEL_PATH = "interview_results.xlsx"
nltk.download('punkt')
nltk.download('stopwords')

# ===== Utility Functions =====
def SpeechToText():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Adjusting for ambient noise...")
            r.adjust_for_ambient_noise(source)
            print("Listening...")
            audio = r.listen(source)
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-IN')
        return query
    except sr.UnknownValueError:
        return "Could not understand the audio."
    except sr.RequestError as e:
        return f"Could not request results from Google Speech Recognition service; {e}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def clean_answer(answer):
    words = word_tokenize(answer)
    stop_words = set(stopwords.words('english'))
    return ' '.join([word for word in words if word.lower() not in stop_words])

def detect_fillers(text):
    common_fillers = {"um", "uh", "like", "you know", "so", "actually", "basically", "literally", "well", "hmm"}
    words = word_tokenize(text.lower())
    used_fillers = [w for w in words if w in common_fillers]
    return ", ".join(set(used_fillers)) if used_fillers else "None"

def validate_answer_with_gemini(question, answer):
    prompt = f"""
    Given the following interview question and the user's answer, evaluate the response:
    
    Question: {question}
    Answer: {answer}

    Provide the following:
    1. Correct Answer
    2. Validation (Valid/Invalid/Partial)
    3. Confidence Score (0 to 1)
    4. Fillers used
    5. Feedback and Improvements

    Format:
    {{
        "correct_answer": "...",
        "validation": "...",
        "confidence_score": 0,
        "fillers": 0,
        "feedback": "..."
    }}
    """
    response = model.generate_content(prompt)
    try:
        result = eval(response.text.strip())
    except:
        result = {
            "correct_answer": "Object-oriented programming (OOP) is defined as a programming paradigm (and not a specific language) built on the concept of objects.",
            "validation": "Correct",
            "fillers": 1,
            "feedback": "Good"
        }
    return result

def append_to_excel(row):
    df = pd.DataFrame([row])
    if os.path.exists(EXCEL_PATH):
        df_existing = pd.read_excel(EXCEL_PATH)
        df_combined = pd.concat([df_existing, df], ignore_index=True)
    else:
        df_combined = df
    df_combined.to_excel(EXCEL_PATH, index=False)

# ===== Routes =====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_questions', methods=['POST'])
def generate_questions():
    job = request.form['job']
    level = request.form['level']
    session['job_title'] = job
    session['difficulty'] = level
    return redirect(url_for('regenerate_questions'))

@app.route('/regenerate_questions')
def regenerate_questions():
    job = session.get('job_title')
    level = session.get('difficulty')

    prompt = f"Generate 10 interview questions for the job role: {job} with difficulty level: {level}. Only provide the questions, numbered 1 to 10, with no additional text, comments, or explanations."
    response = model.generate_content(prompt)
    raw_questions = response.text.strip().split('\n')

    questions = [q.split(". ", 1)[-1].strip() if ". " in q else q.strip() for q in raw_questions if q.strip()]
    session['questions'] = questions

    columns = ["Q.ID", "Question", "User Answer", "Actual Answer", "Confidence Score", "Validation", "Feedback/Improvements", "Fillers Used"]
    df = pd.DataFrame(columns=columns)
    df.to_excel(EXCEL_PATH, index=False)

    question_rows = [{
        "Q.ID": idx + 1,
        "Question": q,
        "User Answer": "",
        "Actual Answer": "",
        "Confidence Score": "",
        "Validation": "",
        "Feedback/Improvements": "",
        "Fillers Used": ""
    } for idx, q in enumerate(questions)]

    df_questions = pd.DataFrame(question_rows)
    df_questions.to_excel(EXCEL_PATH, index=False)

    return redirect(url_for('questions'))

@app.route('/questions')
def questions():
    questions = session.get('questions', [])
    job = session.get('job_title')
    difficulty = session.get('difficulty')
    question_list = list(enumerate(questions, start=1))
    return render_template('questions.html', questions=question_list, job_title=job, difficulty=difficulty)

@app.route('/interview/<int:qid>')
def interview(qid):
    questions = session.get('questions', [])
    if 1 <= qid <= len(questions):
        question = questions[qid - 1]
    else:
        question = 'No question found'
    return render_template('interview.html', question=question, qid=qid)

@app.route('/get_analysis', methods=['POST'])
def get_analysis():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file"}), 400

    audio_file = request.files['audio']
    audio_path = "user_audio.wav"
    audio_file.save(audio_path)

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        transcribed_text = recognizer.recognize_google(audio)
        duration = 10  # Optional duration value
    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand audio."}), 400
    except sr.RequestError as e:
        return jsonify({"error": f"Speech recognition failed: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    return jsonify({
        "transcription": transcribed_text,
        "duration": duration
    })


def extract_field(text, field_name):
    pattern = rf"{field_name}:(.*?)(?=\n[A-Z][a-z ]*?:|\Z)"  # Greedy match until next field or end
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else "Not found"

@app.route('/submit_answer/<qid>', methods=['POST'])
def submit_answer(qid):
    user_answer = request.form.get('answer', '').strip()

    prompt = f"""
    You are an expert interviewer. Given the question ID {qid} and the user's answer below, analyze the answer and provide a concise, accurate JSON response with the following keys:

    {{
        "correct_answer": "Concise ideal answer to the question.",
        "validation": "Valid" or "Invalid" or "Partial",
        "fillers_used": ["um", "like", "you know", ...],
        "feedback": "Brief feedback highlighting strengths and areas for improvement."
    }}

    Question ID: {qid}
    User Answer: "{user_answer}"

    Return only valid JSON without any extra text.
    """

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # Use regex to extract JSON object from raw_text
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            result = json.loads(json_str)
        else:
            raise ValueError("No JSON object found in response.")

    except Exception as e:
        # Fallback response if parsing fails
        result = {
            "correct_answer": "Unable to parse response. Please try again.",
            "validation": "Unknown",
            "fillers_used": [],
            "feedback": "N/A"
        }

    return jsonify({
        'user_answer': user_answer,
        'validation_result': {
            'correct_answer': result.get('correct_answer', ''),
            'validation': result.get('validation', ''),
            'feedback': result.get('feedback', '')
        },
        'fillers_used': result.get('fillers_used', [])
    })
# ===== Run App =====
if __name__ == '__main__':
    app.run(debug=True)
