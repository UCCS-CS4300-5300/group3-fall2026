const codeDialog = document.getElementById('code-dialog');
const dialogTitle = document.getElementById('code-dialog-title');
const codeInput = document.getElementById('code-input');
const codeOutput = document.getElementById('code-output');
const openButton = document.getElementById('code-open');
const runButton = document.getElementById('code-run');
const closeButton = document.getElementById('code-close');
const resetButton = document.getElementById('lesson-reset');

const exerciseDetails = document.getElementById('exercise-details');
const exerciseObject = document.getElementById('exercise-object');
const exerciseTask = document.getElementById('exercise-task');
const exerciseExpectedSection = document.getElementById('exercise-expected-section');
const exerciseExpected = document.getElementById('exercise-expected');
const exerciseHint = document.getElementById('exercise-hint');
const exerciseFeedback = document.getElementById('exercise-feedback');

const task = document.getElementById('screen-task');
const status = document.getElementById('screen-status');

const exercises = JSON.parse(document.getElementById('screen-exercises').textContent);
// Free code written with "Write Code" is saved under this key; exercise code under its exercise ID.
const FREE_CODE = '';

// Saved workspaces are {code: {exerciseId: "..."}}; older Blockly saves have no code and start empty.
const savedWorkspace = JSON.parse(document.getElementById('screen-workspace-state').textContent);
const codeByExercise = savedWorkspace?.code && typeof savedWorkspace.code === 'object' ? savedWorkspace.code : {};
let currentExercise = null;

document.querySelectorAll('form[data-save-workspace]').forEach(form => {
  form.addEventListener('submit', () => {
    form.elements.namedItem('workspace_json').value = JSON.stringify({code: codeByExercise});
  });
});

function startingCode(exercise) {
  return exercise ? exercise.starting_code : '';
}

function objectButton(exercise) {
  return document.querySelector(`.room-object[data-exercise-id="${CSS.escape(exercise.id)}"]`);
}

function isSolved(exercise) {
  return objectButton(exercise)?.classList.contains('solved');
}

// Open the code box for a room object's exercise, or for free code when exercise is null.
function openCodeDialog(exercise) {
  currentExercise = exercise;
  const key = exercise ? exercise.id : FREE_CODE;
  codeInput.value = codeByExercise[key] ?? startingCode(exercise);
  dialogTitle.textContent = exercise ? exercise.title : 'Python code';
  exerciseDetails.hidden = !exercise;
  if (exercise) {
    exerciseObject.textContent = exercise.object;
    exerciseTask.textContent = exercise.task;
    exerciseExpectedSection.hidden = !exercise.expected_output;
    exerciseExpected.textContent = exercise.expected_output;
    exerciseHint.textContent = exercise.hint;
    exerciseHint.closest('details').open = false;
  }
  exerciseFeedback.textContent = exercise && isSolved(exercise) ? '✓ Already solved.' : '';
  codeOutput.textContent = '';
  codeDialog.showModal();
  codeInput.focus();
}

// POST the code as JSON to /check/; exercises also send their room so the server can record success.
async function fetchExecResult(code, exercise) {
  const body = exercise ? {
    code,
    exercise_id: exercise.id,
    mission_id: Number(task.dataset.missionId),
    room_id: Number(task.dataset.roomId)
  } : {code};
  const response = await fetch(task.dataset.checkUrl, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': task.dataset.csrfToken},
    body: JSON.stringify(body)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'The program could not be run.');
  return data;
}

// Show the program's output and error, then the exercise feedback and any final variable values.
function showResult(result, exercise) {
  codeOutput.textContent = (result.output || '') + (result.error || '') || '(no output)';
  if (!exercise) {
    status.textContent = result.error ? '✗ Your program raised an error.' : '✓ Your program ran.';
    return;
  }
  const variableValues = result.variables ? Object.entries(result.variables)
    // Spell booleans the Python way, as the player wrote them.
    .map(([name, value]) => `${name} = ${typeof value === 'boolean' ? (value ? 'True' : 'False') : value}`)
    .join(', ') : '';
  exerciseFeedback.textContent = variableValues ? `${result.feedback} ${variableValues}` : result.feedback;
  if (result.passed) {
    objectButton(exercise)?.classList.add('solved');
  }
  if (result.room_completed) {
    status.textContent = '✓ Room cleared! You can move on.';
  }
}

openButton.addEventListener('click', () => openCodeDialog(null));

document.querySelectorAll('.room-object').forEach(button => {
  const exercise = exercises.find(candidate => candidate.id === button.dataset.exerciseId);
  button.addEventListener('click', () => openCodeDialog(exercise));
});

codeInput.addEventListener('input', () => {
  codeByExercise[currentExercise ? currentExercise.id : FREE_CODE] = codeInput.value;
});

// Tab indents with four spaces instead of leaving the box, since Python depends on indentation.
codeInput.addEventListener('keydown', event => {
  if (event.key !== 'Tab' || event.shiftKey) return;
  event.preventDefault();
  codeInput.setRangeText('    ', codeInput.selectionStart, codeInput.selectionEnd, 'end');
  codeInput.dispatchEvent(new Event('input'));
});

closeButton.addEventListener('click', () => codeDialog.close());

runButton.addEventListener('click', async () => {
  const exercise = currentExercise;
  runButton.disabled = true;
  codeOutput.textContent = 'Running your program...';
  exerciseFeedback.textContent = '';
  try {
    showResult(await fetchExecResult(codeInput.value, exercise), exercise);
  } catch (error) {
    console.error('[screen] Run failed', error);
    codeOutput.textContent = error.message || 'Something went wrong running your program.';
  } finally {
    runButton.disabled = false;
  }
});

resetButton.addEventListener('click', () => {
  status.textContent = '';
  codeOutput.textContent = '';
});
