// =======================================================================
// Convert recorded action units into slots within the configured duration
// =======================================================================
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

  for (const event of result.events) {
    const startTurn = event.before.turn;
    const endTurn = event.after.turn;
    const expectedUnits = event.kind === 'action' ? 1 : 0;
    if (startTurn !== previousTurn || endTurn - startTurn !== expectedUnits || endTurn > units) {
      throw new Error('The encounter execution record has invalid action boundaries.');
    }
    steps.push({event: event, startMs: startTurn * unitDuration, endMs: endTurn * unitDuration});
    previousTurn = endTurn;
  }

  return {
    steps: steps,
    durationMs: previousTurn * unitDuration,
    unitDurationMs: unitDuration
  };
}

// ========================================================================
// Play recorded slots against elapsed wall time instead of counting frames
// ========================================================================
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
            const fraction = (elapsed - step.startMs) / (step.endMs - step.startMs);
            const progress = step.event.before.progress
              + (step.event.after.progress - step.event.before.progress) * fraction;
            callbacks.render(progress, step.event.before.phase);
            frame = clock.requestFrame(refresh);
            return;
          }
        }
        current.stepStarted = true;
        callbacks.showEvent(step.event, step.event.before);
      }

      if (elapsed < step.endMs) {
        const fraction = (elapsed - step.startMs) / (step.endMs - step.startMs);
        const progress = step.event.before.progress
          + (step.event.after.progress - step.event.before.progress) * fraction;
        callbacks.render(progress, step.event.before.phase);
        frame = clock.requestFrame(refresh);
        return;
      }

      callbacks.render(step.event.after.progress, step.event.after.phase);
      callbacks.showEvent(step.event, step.event.after);
      current.index += 1;
      current.stepStarted = false;
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
