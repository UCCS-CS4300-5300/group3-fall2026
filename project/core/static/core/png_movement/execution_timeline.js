// =======================================================================
// Fit block highlights into the zombie's existing action-unit intervals
// =======================================================================
// This fraction is a display allocation, not extra encounter time. Conditions
// before an action share the first quarter of its unit; the action owns the rest.
const DECISION_FRACTION = 0.25;

export function buildExecutionTimeline(result, durationMs) {
  const units = result.state.action_units;
  if (!Number.isInteger(units) || units < 1 || !Number.isFinite(durationMs) || durationMs <= 0) {
    throw new Error('The encounter has invalid animation timing.');
  }
  if (!Array.isArray(result.events) || result.events.length === 0) {
    throw new Error('The encounter has no recorded execution events.');
  }

  const unitDuration = durationMs / units;
  const steps = [];
  let previousTurn = 0;
  let decisions = [];

  for (const event of result.events) {
    const startTurn = event.before.turn;
    const endTurn = event.after.turn;
    const expectedUnits = event.kind === 'action' ? 1 : 0;
    if (startTurn !== previousTurn || endTurn - startTurn !== expectedUnits || endTurn > units) {
      throw new Error('The encounter execution record has invalid action boundaries.');
    }
    previousTurn = endTurn;

    if (event.kind !== 'action') {
      // The evaluator also records if/switch/case traversal. Those containers
      // are not condition expressions and must not take any highlight time
      // away from the Boolean blocks the player actually sees being checked.
      if (event.kind === 'condition') decisions.push(event);
      continue;
    }

    // Motion spans the full action unit even while its preceding decisions are
    // highlighted. Display steps reference this interval rather than each
    // decision's equal before/after progress, which would freeze the zombie.
    const motion = {event, startMs: startTurn * unitDuration, endMs: endTurn * unitDuration};
    const decisionDuration = decisions.length ? unitDuration * DECISION_FRACTION : 0;
    const eachDecision = decisions.length ? decisionDuration / decisions.length : 0;

    for (const [index, decision] of decisions.entries()) {
      steps.push({
        event: decision,
        startMs: motion.startMs + index * eachDecision,
        endMs: motion.startMs + (index + 1) * eachDecision,
        motion
      });
    }
    steps.push({event, startMs: motion.startMs + decisionDuration, endMs: motion.endMs, motion});
    decisions = [];
  }

  // A trailing decision has no following movement interval. Report it at the
  // final boundary without extending the animation or inventing another unit.
  const endMs = previousTurn * unitDuration;
  for (const event of decisions) {
    const motion = {event, startMs: endMs, endMs};
    steps.push({event, startMs: endMs, endMs, motion});
  }

  return {steps, durationMs: endMs, unitDurationMs: unitDuration};
}

// ========================================================================
// Play motion and highlight intervals from the same elapsed animation time
// ========================================================================
// showEvent(event, state, boundary) reports each highlight's 'start' and 'end'.
// render(progress, phase) follows the containing action unit, not the highlight
// duration. A conditional can therefore glow without pausing/slowing movement.
export function createExecutionTimelinePlayer(callbacks, clock) {
  let current = null;
  let frame = null;

  function clearFrame() {
    if (frame !== null) clock.cancelFrame(frame);
    frame = null;
  }

  function cancel() {
    clearFrame();
    if (!current) return;
    const resolve = current.resolve;
    current = null;
    resolve({completed: false, missedBlockId: null});
  }

  /** Render a highlight step at an absolute position on the animation clock. */
  function renderStep(step, timeMs) {
    const motion = step.motion;
    const duration = motion.endMs - motion.startMs;
    const fraction = duration > 0
      ? Math.min(1, Math.max(0, (timeMs - motion.startMs) / duration)) : 1;
    const before = motion.event.before;
    const after = motion.event.after;
    callbacks.render(
      before.progress + (after.progress - before.progress) * fraction,
      fraction === 1 ? after.phase : before.phase
    );
  }

  function refresh() {
    clearFrame();
    if (!current) return;

    // A background tab can miss frames; elapsed time continues to increase.
    const elapsed = Math.max(0, clock.now() - current.startedAt);
    const steps = current.timeline.steps;

    while (current.index < steps.length) {
      const step = steps[current.index];
      if (!current.stepStarted) {
        // A timed action must begin during its slot, while execution is visible.
        // Expired combat actions fail instead of being replayed in a catch-up loop.
        if (step.event.requires_timing === true) {
          if (elapsed >= step.endMs) {
            callbacks.render(step.event.after.progress, 'failed');
            const resolve = current.resolve;
            current = null;
            resolve({completed: true, missedBlockId: step.event.block_id});
            return;
          }
          if (clock.isHidden()) {
            renderStep(step, elapsed);
            frame = clock.requestFrame(refresh);
            return;
          }
        }
        current.stepStarted = true;
        callbacks.showEvent(step.event, step.event.before, 'start');
      }

      if (elapsed < step.endMs) {
        renderStep(step, elapsed);
        frame = clock.requestFrame(refresh);
        return;
      }

      renderStep(step, step.endMs);
      callbacks.showEvent(step.event, step.event.after, 'end');
      current.index += 1;
      current.stepStarted = false;
    }

    // Blocks are finished, but noise may have started an unfinished approach.
    // Continue at the recorded rate using the same clock and frame scheduler.
    const lastStep = steps.at(-1);
    const finalState = lastStep?.event.after;
    if (finalState?.time > 0 && finalState.progress < 1
        && finalState.phase !== 'failed' && finalState.phase !== 'defeated') {
      const approachDuration = current.timeline.unitDurationMs * finalState.action_units;
      const progress = Math.min(1,
        finalState.progress + (elapsed - lastStep.endMs) / approachDuration);
      callbacks.render(progress, finalState.phase);
      if (progress < 1) {
        frame = clock.requestFrame(refresh);
        return;
      }
    }

    const resolve = current.resolve;
    current = null;
    resolve({completed: true, missedBlockId: null});
  }

  function play(timeline) {
    cancel();
    return new Promise(resolve => {
      current = {
        timeline: timeline,
        resolve: resolve,
        startedAt: clock.now(),
        index: 0,
        stepStarted: false
      };
      refresh();
    });
  }

  function isRunning() {
    return current !== null;
  }

  return {play: play, refresh: refresh, cancel: cancel, isRunning: isRunning};
}
