const questions = Array.from(document.querySelectorAll('.question-card'));
const timerElement = document.getElementById('timer');
const prevButton = document.getElementById('prev-btn');
const nextButton = document.getElementById('next-btn');
const quizForm = document.getElementById('quiz-form');
const timeTakenInput = document.getElementById('time_taken');
const clientScoreInput = document.getElementById('client_score');
let currentIndex = 0;
let remainingTime = Number(timeTakenInput.value);
let intervalId;

function showQuestion(index) {
  questions.forEach((q, idx) => {
    q.style.display = idx === index ? 'block' : 'none';
  });
  currentIndex = index;
}

function updateTimer() {
  const minutes = String(Math.floor(remainingTime / 60)).padStart(2, '0');
  const seconds = String(remainingTime % 60).padStart(2, '0');
  timerElement.textContent = `${minutes}:${seconds}`;
  if (remainingTime <= 0) {
    clearInterval(intervalId);
    submitQuiz();
  }
}

function calculateScore() {
  let score = 0;
  questions.forEach((question) => {
    const correct = question.dataset.correct;
    const selected = question.querySelector('input[type="radio"]:checked');
    if (selected && selected.value === correct) {
      score += 1;
    }
  });
  return score;
}

function submitQuiz() {
  clientScoreInput.value = calculateScore();
  timeTakenInput.value = remainingTime;
  quizForm.submit();
}

prevButton.addEventListener('click', () => {
  if (currentIndex > 0) {
    showQuestion(currentIndex - 1);
  }
});

nextButton.addEventListener('click', () => {
  if (currentIndex < questions.length - 1) {
    showQuestion(currentIndex + 1);
  }
});

quizForm.addEventListener('submit', (event) => {
  clientScoreInput.value = calculateScore();
  timeTakenInput.value = remainingTime;
});

showQuestion(currentIndex);
intervalId = setInterval(() => {
  remainingTime -= 1;
  updateTimer();
}, 1000);
updateTimer();
