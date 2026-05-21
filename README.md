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
3. Copy `.env.example` to `.env` and set your values.
4. Run the app:
   ```powershell
   python app.py
   ```
5. Open the app in your browser at `http://127.0.0.1:5000`

### Database configuration

The project uses SQLAlchemy and defaults to SQLite at `instance/quiz.db`.
Configuration is loaded from environment variables, and `.env` files are supported.

1. Create a `.env` file in the project root.
2. Add database or secret values:

```powershell
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///instance/quiz.db
```

You can also use a custom database URL:

```powershell
$env:DATABASE_URL = "postgresql://user:password@localhost/dbname"
python app.py
```

For local development, `DATABASE_URL` can point to any SQLAlchemy-compatible database.

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
