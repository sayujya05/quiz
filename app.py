from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from datetime import datetime
import json
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quiz.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), nullable=False, default="student")

    @property
    def is_teacher(self):
        return self.is_admin or self.role == "teacher"

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    options = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(120), nullable=False, default="General")

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    time_taken = db.Column(db.Integer, nullable=False)
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("scores", lazy=True))

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
QUIZ_TIME_SECONDS = 30
QUIZ_QUESTION_COUNT = 5

def setup_database():
    with app.app_context():
        db.create_all()
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(user)"))
            user_columns = [row[1] for row in result]
            if "role" not in user_columns:
                conn.execute(text("ALTER TABLE user ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'student'"))
            result = conn.execute(text("PRAGMA table_info(question)"))
            question_columns = [row[1] for row in result]
            if "category" not in question_columns:
                conn.execute(text("ALTER TABLE question ADD COLUMN category VARCHAR(120) NOT NULL DEFAULT 'General'"))
        if not User.query.filter_by(username=ADMIN_USERNAME).first():
            admin = User(
                username=ADMIN_USERNAME,
                password_hash=generate_password_hash(ADMIN_PASSWORD),
                is_admin=True,
                role="teacher",
            )
            db.session.add(admin)
            db.session.commit()

setup_database()

def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)

@app.context_processor
def inject_current_user():
    return dict(current_user=current_user())

@app.template_filter('loads')
def loads_filter(value):
    try:
        return json.loads(value)
    except Exception:
        return []

def login_required(route):
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return route(*args, **kwargs)
    wrapper.__name__ = route.__name__
    return wrapper

def admin_required(route):
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or not user.is_teacher:
            flash("Teacher access required.", "warning")
            return redirect(url_for("index"))
        return route(*args, **kwargs)
    wrapper.__name__ = route.__name__
    return wrapper

@app.route("/")
def index():
    user = current_user()
    question_count = Question.query.count()
    categories = [row[0] for row in db.session.query(Question.category).distinct().order_by(Question.category).all()]
    return render_template("index.html", user=user, question_count=question_count, categories=categories)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "student").strip().lower()
        if role not in ("student", "teacher"):
            role = "student"
        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return redirect(url_for("register"))
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        flash("Account created successfully.", "success")
        return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid username or password.", "danger")
            return redirect(url_for("login"))
        session["user_id"] = user.id
        flash("Logged in successfully.", "success")
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out.", "info")
    return redirect(url_for("index"))

@app.route("/quiz")
@login_required
def quiz():
    category = request.args.get("category", "")
    if category:
        questions = Question.query.filter_by(category=category).all()
    else:
        questions = Question.query.all()
    if not questions:
        flash("No quiz questions available for that category.", "warning")
        return redirect(url_for("index"))
    selected = questions
    if len(questions) > QUIZ_QUESTION_COUNT:
        selected = random.sample(questions, QUIZ_QUESTION_COUNT)
    random.shuffle(selected)
    session["quiz_question_ids"] = [q.id for q in selected]
    return render_template(
        "quiz.html",
        questions=selected,
        time_limit=QUIZ_TIME_SECONDS,
        category=category,
    )

@app.route("/submit_quiz", methods=["POST"])
@login_required
def submit_quiz():
    user = current_user()
    question_ids = session.get("quiz_question_ids", [])
    submitted_answers = {}
    for key, value in request.form.items():
        if key.startswith("question_"):
            qid = int(key.split("_")[1])
            submitted_answers[qid] = value
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    score = 0
    for question in questions:
        answer = submitted_answers.get(question.id, "")
        if answer == question.correct_answer:
            score += 1
    total = len(questions)
    time_taken = int(request.form.get("time_taken", QUIZ_TIME_SECONDS))
    new_score = Score(
        user_id=user.id,
        score=score,
        total=total,
        time_taken=max(0, QUIZ_TIME_SECONDS - time_taken),
    )
    db.session.add(new_score)
    db.session.commit()
    return render_template(
        "result.html",
        score=score,
        total=total,
        correct=score,
        time_remaining=time_taken,
    )

@app.route("/leaderboard")
def leaderboard():
    top_scores = (
        Score.query.order_by(Score.score.desc(), Score.time_taken.asc())
        .limit(20)
        .all()
    )
    return render_template("leaderboard.html", top_scores=top_scores)

@app.route("/admin")
@admin_required
def admin():
    questions = Question.query.order_by(Question.id.asc()).all()
    return render_template("admin.html", questions=questions)

@app.route("/admin/add", methods=["POST"])
@admin_required
def admin_add():
    text = request.form.get("text", "").strip()
    option_a = request.form.get("option_a", "").strip()
    option_b = request.form.get("option_b", "").strip()
    option_c = request.form.get("option_c", "").strip()
    option_d = request.form.get("option_d", "").strip()
    correct = request.form.get("correct", "").strip()
    category = request.form.get("category", "General").strip() or "General"
    if not text or not option_a or not option_b or not correct:
        flash("Please provide a question, at least two options, and a correct answer.", "danger")
        return redirect(url_for("admin"))
    options = json.dumps([option_a, option_b, option_c, option_d])
    question = Question(text=text, options=options, correct_answer=correct, category=category)
    db.session.add(question)
    db.session.commit()
    flash("Question added.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/edit/<int:question_id>", methods=["GET", "POST"])
@admin_required
def admin_edit(question_id):
    question = Question.query.get_or_404(question_id)
    if request.method == "POST":
        question.text = request.form.get("text", question.text).strip()
        option_a = request.form.get("option_a", "").strip()
        option_b = request.form.get("option_b", "").strip()
        option_c = request.form.get("option_c", "").strip()
        option_d = request.form.get("option_d", "").strip()
        question.correct_answer = request.form.get("correct", question.correct_answer).strip()
        question.category = request.form.get("category", question.category).strip() or question.category
        question.options = json.dumps([option_a, option_b, option_c, option_d])
        db.session.commit()
        flash("Question updated.", "success")
        return redirect(url_for("admin"))
    options = json.loads(question.options)
    return render_template("edit_question.html", question=question, options=options)

@app.route("/admin/delete/<int:question_id>", methods=["POST"])
@admin_required
def admin_delete(question_id):
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted.", "info")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)
