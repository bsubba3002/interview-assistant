Interview Analysis Web Application – Technical Documentation
Overview
This web application is designed to simulate an interview experience using AI-driven question generation, speech-to-text analysis, and response validation. It integrates Google Gemini AI, speech recognition, and NLP tools to assess user answers and provide feedback.

System Architecture
1. Frontend
Built using HTML templates rendered by Flask (render_template).

Allows users to:

Enter job roles and experience level.

View dynamically generated interview questions.

Record and submit audio answers.

Receive instant validation and feedback.

2. Backend
Built with Flask as the web framework.

Includes:

Route handling for form submissions and navigation.

Session management to store user data across pages.

Audio processing and transcription.

AI integration for question generation and answer validation.

3. AI & NLP Integration
Google Gemini AI is used to:

Generate domain-specific interview questions.

Evaluate and validate user answers based on correctness and fluency.

Speech Recognition:

Converts user audio input to text using Google’s speech-to-text engine.

Natural Language Processing:

Tokenization and filler word detection (via NLTK).

Feedback generation using AI models.

4. Data Storage
All interview responses, evaluations, and metadata are stored in an Excel file (interview_results.xlsx) using Pandas.

Each row records:

Question ID and content.

User's transcribed answer.

Correct answer.

Validation result.

Confidence score.

Feedback and detected filler words.

Core Functional Modules
1. Question Generation
Prompt sent to Gemini AI to create 10 questions based on:

Job role (e.g., Data Scientist).

Difficulty level (e.g., Beginner, Intermediate, Expert).

2. Interview Process
Users select questions and submit answers through a microphone.

Audio is transcribed and analyzed before being sent to Gemini AI for evaluation.

3. Answer Evaluation
Gemini AI returns:

A model answer.

Validation status (Valid, Partial, Invalid).

Feedback for improvement.

List of filler words used.

4. Report Generation
Responses and AI feedback are compiled into an Excel spreadsheet.

Intended for post-interview review or reporting.

Key Libraries and Tools
Library	Purpose
Flask	Web application framework
Google Generative AI	AI model for question and feedback generation
SpeechRecognition	Audio transcription
NLTK	NLP (tokenization, stopword removal, etc.)
Pandas	Data manipulation and Excel file handling
ReportLab	(Planned/future) PDF generation
OpenAI/Gemini API Key	Access to LLM for content generation
