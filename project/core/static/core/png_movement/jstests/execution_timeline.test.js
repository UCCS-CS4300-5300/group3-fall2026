import {expect, test} from 'vitest';
import {buildExecutionTimeline, createExecutionTimelinePlayer} from '../execution_timeline.js';

function timelineHarness(callbacks = {}) {
  const first = {turn: 0, progress: 0, phase: 'approaching'};
  const attacking = {turn: 1, progress: 0.5, phase: 'attacking'};
  const defended = {turn: 2, progress: 1, phase: 'defended'};
  const result = {
    state: {turn: 2, action_units: 2},
    events: [
      {block_id: 'approach', kind: 'action', before: first, after: attacking},
      {block_id: 'choice', kind: 'condition', before: attacking, after: attacking},
      {block_id: 'defense', kind: 'action', requires_timing: true, before: attacking, after: defended}
    ]
  };
  let now = 0;
  let hidden = false;
  const player = createExecutionTimelinePlayer({render() {}, showEvent() {}, ...callbacks}, {
    now: () => now,
    isHidden: () => hidden,
    requestFrame: () => 1,
    cancelFrame() {}
  });
  function frameAt(time, hide) {
    now = time;
    hidden = hide === true;
    player.refresh();
  }
  return {player: player, timeline: buildExecutionTimeline(result, 1000), frameAt: frameAt};
}

test('conditional highlights fit inside the configured zombie animation duration', async () => {
  const clock = timelineHarness();
  const playback = clock.player.play(clock.timeline);
  clock.frameAt(500);
  clock.frameAt(625);
  clock.frameAt(1000);
  expect(clock.timeline.unitDurationMs).toBe(500);
  expect(clock.timeline.durationMs).toBe(1000);
  expect(clock.timeline.steps[1].event.before.turn).toBe(clock.timeline.steps[1].event.after.turn);
  expect(await playback).toEqual({completed: true, missedBlockId: null});
});

test('zombie progress stays tied to animation time during conditional highlights', async () => {
  const starts = [];
  let progress;
  const boundaries = [];
  const clock = timelineHarness({
    render(value) { progress = value; },
    showEvent(event, _state, boundary) {
      boundaries.push([event.block_id, boundary]);
      if (boundary === 'start') starts.push(event.block_id);
    }
  });
  const playback = clock.player.play(clock.timeline);
  clock.frameAt(250);
  expect(progress).toBe(0.25);
  expect(starts).toEqual(['approach']);
  clock.frameAt(500);
  expect(progress).toBe(0.5);
  expect(boundaries).toEqual([
    ['approach', 'start'], ['approach', 'end'],
    ['choice', 'start']
  ]);
  clock.frameAt(600);
  expect(progress).toBe(0.6);
  expect(starts).toEqual(['approach', 'choice']);
  clock.frameAt(625);
  expect(boundaries.slice(-2)).toEqual([['choice', 'end'], ['defense', 'start']]);
  clock.frameAt(750);
  expect(progress).toBe(0.75);
  clock.frameAt(1000);
  await playback;
  expect(boundaries.at(-1)).toEqual(['defense', 'end']);
});

test('a hidden combat window is missed rather than replayed after return', async () => {
  const clock = timelineHarness();
  const playback = clock.player.play(clock.timeline);
  clock.frameAt(625, true);
  clock.frameAt(1400);
  expect(await playback).toEqual({completed: true, missedBlockId: 'defense'});
});

test('a frame stall can miss the defense window while visible too', async () => {
  const clock = timelineHarness();
  const playback = clock.player.play(clock.timeline);
  clock.frameAt(1400);
  expect(await playback).toEqual({completed: true, missedBlockId: 'defense'});
});

test('cancellation settles playback without completing the encounter', async () => {
  const clock = timelineHarness();
  const playback = clock.player.play(clock.timeline);
  clock.player.cancel();
  clock.frameAt(1000);
  expect(await playback).toEqual({completed: false, missedBlockId: null});
  expect(clock.player.isRunning()).toBe(false);
});


test('only conditions share the highlight prefix; containers consume no display time', () => {
  const before = {turn: 0, progress: 0, phase: 'approaching'};
  const after = {turn: 1, progress: 1, phase: 'defeated'};
  const timeline = buildExecutionTimeline({
    state: {action_units: 1},
    events: [
      ...['condition', 'if', 'condition', 'switch', 'case'].map((kind, index) => ({
        block_id: `decision-${index}`, kind, before, after: before
      })),
      {block_id: 'action', kind: 'action', before, after}
    ]
  }, 1200);
  expect(timeline.steps.map(step => [step.startMs, step.endMs]))
    .toEqual([[0, 150], [150, 300], [300, 1200]]);
  expect(timeline.steps.map(step => step.event.block_id))
    .toEqual(['decision-0', 'decision-2', 'action']);
  expect(timeline.durationMs).toBe(1200);
  expect(timeline.steps.every(step => step.motion === timeline.steps[0].motion)).toBe(true);
});
