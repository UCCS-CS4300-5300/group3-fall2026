import {createWorkspaceController} from '../blockly/workspace_controller.js';
import {showRunFeedback} from './run_feedback.js';
import {installBossExitNavigation, markBossExitComplete} from './boss_exit.js';
import {initializeMovement} from '@png-movement/png_move.js';

// ========================================================================
// Own the attempt lifecycle so screen controls only signal Start and Reset
// ========================================================================
export function createEncounterController(root) {
  const task = root.getElementById('screen-task');
  const status = root.getElementById('screen-status');
  const runButton = root.getElementById('lesson-run');
  const bossExit = root.querySelector('.boss-exit');
  const view = root.defaultView;
  const policy = readPageData(root, 'screen-workspace-config');
  const initialVariables = readPageData(root, 'screen-initial-variables');
  const movementSettings = readPageData(root, 'screen-movement-config');
  const workspace = createWorkspaceController(root, policy, initialVariables, movementSettings);
  const movement = initializeMovement(root);
  const usesContinuousPlayback = policy.playback === 'continuous';
  const usesTimelinePlayback = policy.playback === 'timeline';
  let generation = 0;
  let pendingRequest = null;
  let runPending = false;
  let destroyed = false;

  function updateRunAvailability() {
    runButton.disabled = destroyed || runPending
      || ((usesContinuousPlayback || usesTimelinePlayback) && !movement.isReady());
  }

  // ===========================================================================
  // Cancel stale requests before a retry, reset, or navigation can replace them
  // ===========================================================================
  function cancelPendingRun() {
    generation += 1;
    if (pendingRequest) pendingRequest.abort();
    movement.cancelExecution();
    workspace.setLocked(false);
    pendingRequest = null;
    runPending = false;
    updateRunAvailability();
  }

  function resetAttempt() {
    if (destroyed) return;
    cancelPendingRun();
    movement.reset();
    status.textContent = '';
    updateRunAvailability();
  }

  // =====================================================================
  // Submit the collected program and let the server determine the outcome
  // =====================================================================
  async function requestProgramResult(submission, signal) {
    const response = await fetch(task.dataset.checkUrl, {
      method: 'POST',
      signal: signal,
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': task.dataset.csrfToken},
      body: JSON.stringify(submission)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'The program could not be run.');
    return result;
  }

  // ====================================================================
  // Show recorded state changes without adding the Stage 5 block pointer
  // ====================================================================
  function showExecutionState(event, state) {
    let message = `Action units: ${state.turn}/${state.action_units}.`;
    if (event.kind === 'action') message = `Action: ${event.result}(). ` + message;
    if (Object.hasOwn(state, 'attack_type')) {
      const attack = state.attack_type || 'not revealed';
      message += ` Attack: ${attack}.`;
    }
    status.textContent = message;
  }

  function confirmPlaybackOutcome(result, outcome, signal) {
    const submission = {
      mission_id: Number(task.dataset.missionId),
      room_id: Number(task.dataset.roomId),
      finish_playback: result.playback_id
    };
    if (outcome.missedBlockId !== null) submission.missed_block = outcome.missedBlockId;
    return requestProgramResult(submission, signal);
  }

  // ===========================================================================
  // Start an attempt and coordinate submission, playback, feedback, and success
  // ===========================================================================
  async function startAttempt() {
    if (destroyed) return;
    cancelPendingRun();
    const attemptGeneration = generation;
    const request = new AbortController();
    pendingRequest = request;
    runPending = true;
    updateRunAvailability();
    status.textContent = 'Running your program...';

    let playbackAttempt = null;
    try {
      const submission = workspace.collectProgram(task.dataset);
      workspace.setLocked(true);
      if (usesContinuousPlayback) playbackAttempt = movement.start(initialVariables.zombie_speed);

      let result = await requestProgramResult(submission, request.signal);
      if (attemptGeneration !== generation) return;

      if (usesContinuousPlayback) movement.applyResult(playbackAttempt, result);
      if (usesTimelinePlayback) {
        const outcome = await movement.playExecution(result, showExecutionState);
        if (attemptGeneration !== generation || !outcome.completed) return;
        result = await confirmPlaybackOutcome(result, outcome, request.signal);
        if (attemptGeneration !== generation) return;
      }
      markBossExitComplete(result, bossExit);
      showRunFeedback(status, result);
    } catch (error) {
      if (attemptGeneration !== generation) return;

      if (usesContinuousPlayback && playbackAttempt !== null) movement.fail(playbackAttempt);
      status.textContent = error.message || 'Something went wrong running your program.';
    } finally {
      if (attemptGeneration === generation) {
        pendingRequest = null;
        runPending = false;
        workspace.setLocked(false);
        updateRunAvailability();
      }
    }
  }

  // ==========================================================================
  // Save navigation state and release listeners when the controller is removed
  // ==========================================================================
  const removeReadinessListener = movement.onReady(updateRunAvailability);
  const removeExitListener = installBossExitNavigation(bossExit, cancelPendingRun);
  const formListeners = [];

  for (const form of root.querySelectorAll('form[data-save-workspace]')) {
    const saveBeforeNavigation = () => {
      workspace.saveToForm(form);
      if (!bossExit || form !== bossExit.form) resetAttempt();
    };
    form.addEventListener('submit', saveBeforeNavigation);
    formListeners.push({form: form, listener: saveBeforeNavigation});
  }

  function handlePageHide() {
    if (bossExit) cancelPendingRun();
    else resetAttempt();
  }

  view.addEventListener('pagehide', handlePageHide);
  view.addEventListener('resize', workspace.resize);

  function destroy() {
    if (destroyed) return;
    cancelPendingRun();
    destroyed = true;
    if (typeof removeReadinessListener === 'function') removeReadinessListener();
    if (typeof removeExitListener === 'function') removeExitListener();
    for (const entry of formListeners) {
      entry.form.removeEventListener('submit', entry.listener);
    }
    view.removeEventListener('pagehide', handlePageHide);
    view.removeEventListener('resize', workspace.resize);
    movement.destroy();
    workspace.destroy();
    updateRunAvailability();
  }

  return {start: startAttempt, reset: resetAttempt, destroy: destroy};
}

function readPageData(root, id) {
  return JSON.parse(root.getElementById(id).textContent);
}
