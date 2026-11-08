const popup = document.getElementById('exercise-popup');
const exercisesElement = document.getElementById('screen-exercises');
const task = document.getElementById('screen-task');

if (popup && task) {
  const quizButton = document.getElementById('quiz-button');
  const quizPopup = document.getElementById('quiz-popup');
  if (quizButton && quizPopup) {
    quizButton.addEventListener('click', () => quizPopup.showModal());
  }

  // Rooms without exercises still open the popup for the jumpscare's debug exercise.
  const exercises = JSON.parse(exercisesElement?.textContent || '[]') ?? [];
  const code = document.getElementById('exercise-code');
  const status = document.getElementById('exercise-status');
  const runButton = document.getElementById('exercise-run');
  const output = document.getElementById('exercise-output');
  let current = null;

  // Drafts are kept per mission, room, and exercise in this browser only.
  function draftKey(exercise) {
    return `exercise-code:${task.dataset.missionId}:${task.dataset.roomId}:${exercise.id}`;
  }

  function loadDraft(exercise) {
    try {
      return localStorage.getItem(draftKey(exercise));
    } catch {
      return null;
    }
  }

  function saveDraft() {
    if (!current) return;
    try {
      localStorage.setItem(draftKey(current), code.value);
      status.textContent = 'Saved.';
    } catch {
      status.textContent = 'Could not save in this browser.';
    }
  }

  function openExercise(exercise) {
    current = exercise;
    document.getElementById('exercise-title').textContent = `${exercise.id} · ${exercise.title}`;
    document.getElementById('exercise-object').textContent = exercise.object;
    document.getElementById('exercise-task').textContent = exercise.task;
    document.getElementById('exercise-expected').textContent = exercise.expected_output;
    document.getElementById('exercise-hint').textContent = exercise.hint;
    code.value = loadDraft(exercise) ?? exercise.starting_code;
    status.textContent = '';
    output.textContent = '';
    popup.showModal();
    code.focus();
  }

  document.querySelectorAll('.exercise-button').forEach((button) => {
    button.addEventListener('click', () => openExercise(exercises[Number(button.dataset.exerciseIndex)]));
  });
    let jumpscareExercise = null;
  document.addEventListener('jumpscare:debug', (event) => {
    jumpscareExercise = event.detail;
    openExercise(event.detail);
  });
  document.getElementById('exercise-save').addEventListener('click', saveDraft);
  popup.addEventListener('close', saveDraft);

  // Tab indents instead of leaving the box, since Python needs indentation; Esc still closes.
  code.addEventListener('keydown', (event) => {
    if (event.key !== 'Tab' || event.shiftKey) return;
    event.preventDefault();
    code.setRangeText('    ', code.selectionStart, code.selectionEnd, 'end');
  });

  // Send the code to the server, which runs it with exec() and compares the printed output.
  async function runExercise() {
    if (!current) return;
    saveDraft();
    runButton.disabled = true;
    status.textContent = 'Running...';
    output.textContent = '';
    try {
      const response = await fetch(task.dataset.runExerciseUrl, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': task.dataset.csrfToken},
        body: JSON.stringify({
          mission_id: Number(task.dataset.missionId),
          room_id: Number(task.dataset.roomId),
          exercise_id: current.id,
          code: code.value
        })
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.error || 'The code could not be run.');
      output.textContent = [result.output, result.error].filter(Boolean).join('\n');
      
      // Solving the jumpscare's debug defeats the zombie: show ✓ briefly, then play its defeat video.
      if (result.passed && current === jumpscareExercise) {
        jumpscareExercise = null;
        setTimeout(() => {
          popup.close();
          document.dispatchEvent(new CustomEvent('jumpscare:defeated'));
        }, 800);
      }
      if (result.passed) status.textContent = '✓ Correct!';
      else if (result.error) status.textContent = '✗ Your code hit an error.';
      else status.textContent = "✗ Your output doesn't match yet.";
    } catch (error) {
      status.textContent = error.message;
    } finally {
      runButton.disabled = false;
    }
  }

  runButton.addEventListener('click', runExercise);
}