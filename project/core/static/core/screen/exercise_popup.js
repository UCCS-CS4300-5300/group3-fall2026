const popup = document.getElementById('exercise-popup');
const exercisesElement = document.getElementById('screen-exercises');
const task = document.getElementById('screen-task');

if (popup && exercisesElement && task) {
  const exercises = JSON.parse(exercisesElement.textContent);
  const code = document.getElementById('exercise-code');
  const status = document.getElementById('exercise-status');
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
    popup.showModal();
    code.focus();
  }

  document.querySelectorAll('.exercise-button').forEach((button) => {
    button.addEventListener('click', () => openExercise(exercises[Number(button.dataset.exerciseIndex)]));
  });
  document.getElementById('exercise-save').addEventListener('click', saveDraft);
  popup.addEventListener('close', saveDraft);

  // Tab indents instead of leaving the box, since Python needs indentation; Esc still closes.
  code.addEventListener('keydown', (event) => {
    if (event.key !== 'Tab' || event.shiftKey) return;
    event.preventDefault();
    code.setRangeText('    ', code.selectionStart, code.selectionEnd, 'end');
  });
}