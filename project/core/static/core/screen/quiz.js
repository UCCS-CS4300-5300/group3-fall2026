(() => {
const button = document.getElementById('quiz-button');
const dialog = document.getElementById('quiz-popup');
const quizElement = document.getElementById('screen-quiz');
const task = document.getElementById('screen-task');

if (button && dialog && quizElement && task) {
  const questions = JSON.parse(quizElement.textContent || '[]');
  const progress = document.getElementById('quiz-progress');
  const questionText = document.getElementById('quiz-question');
  const choices = document.getElementById('quiz-choices');
  const nextButton = document.getElementById('quiz-next');
  const status = document.getElementById('quiz-status');
  const completion = document.getElementById('quiz-complete');
  const resultText = document.getElementById('quiz-result');
  const restartButton = document.getElementById('quiz-restart');
  let currentQuestion = 0;
  let answers = [];

  function showQuestion() {
    const question = questions[currentQuestion];
    progress.textContent = `Question ${currentQuestion + 1} of ${questions.length}`;
    questionText.textContent = question.question;
    choices.replaceChildren();
    question.choices.forEach((choice, choiceIndex) => {
      const choiceButton = document.createElement('button');
      choiceButton.type = 'button';
      choiceButton.textContent = choice;
      choiceButton.setAttribute('aria-pressed', String(answers[currentQuestion] === choiceIndex));
      choiceButton.addEventListener('click', () => {
        answers[currentQuestion] = choiceIndex;
        choices.querySelectorAll('button').forEach((item, index) => {
          item.setAttribute('aria-pressed', String(index === choiceIndex));
        });
        nextButton.disabled = false;
      });
      choices.appendChild(choiceButton);
    });
    nextButton.disabled = answers[currentQuestion] === undefined;
    nextButton.textContent = currentQuestion === questions.length - 1 ? 'Finish quiz' : 'Next question';
    status.textContent = '';
  }

  function startQuiz() {
    currentQuestion = 0;
    answers = Array(questions.length);
    completion.hidden = true;
    progress.hidden = false;
    questionText.hidden = false;
    choices.hidden = false;
    nextButton.hidden = false;
    showQuestion();
    dialog.showModal();
  }

  async function finishQuiz() {
    nextButton.disabled = true;
    status.textContent = 'Checking your answers...';
    try {
      const response = await fetch(task.dataset.submitQuizUrl, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': task.dataset.csrfToken},
        body: JSON.stringify({
          mission_id: Number(task.dataset.missionId),
          room_id: Number(task.dataset.roomId),
          answers
        })
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.error || 'The quiz could not be scored.');

      progress.hidden = true;
      questionText.hidden = true;
      choices.hidden = true;
      nextButton.hidden = true;
      status.textContent = '';
      resultText.textContent = `You finished all ${result.total} questions. Score: ${result.score} of ${result.total}.`;
      completion.hidden = false;
    } catch (error) {
      status.textContent = error.message;
      nextButton.disabled = false;
    }
  }

  button.addEventListener('click', startQuiz);
  nextButton.addEventListener('click', () => {
    if (answers[currentQuestion] === undefined) return;
    if (currentQuestion === questions.length - 1) {
      finishQuiz();
      return;
    }
    currentQuestion += 1;
    showQuestion();
  });
  restartButton.addEventListener('click', startQuiz);
}
})();