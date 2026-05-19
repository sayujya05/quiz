# Online Quiz / Exam Platform

A simple Flask-based quiz platform with:

- User registration and login
- Admin interface to add, update, and delete quiz questions
- Randomized timed quizzes
- Leaderboard with score tracking

## Setup

1. Create a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Run the app:
   ```powershell
   python app.py
   ```
4. Open the app in your browser at `http://127.0.0.1:5000`

## Production server (optional)

Install `waitress` and run with a real WSGI server:

```powershell
pip install waitress
waitress-serve --listen=127.0.0.1:5000 app:app
```

## Admin account

- Username: `admin`
- Password: `admin123`

## Notes

- The platform stores data in `quiz.db`.
- Quiz timer and navigation are handled in `static/js/quiz.js`.
- Customize questions in the admin UI.
