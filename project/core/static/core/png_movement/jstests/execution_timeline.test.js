import {expect, test} from 'vitest';
import {buildExecutionTimeline, createExecutionTimelinePlayer} from '../execution_timeline.js';

function timelineHarness() {
  const first = {turn: 0, progress: 0, phase: 'approaching'};
  const attacking = {turn: 1, progress: 0.5, phase: 'attacking'};
  const defended = {turn: 2, progress: 1, phase: 'defended'};
  const result = {
    state: {turn: 2, action_units: 2},
    events: [
      {block_id: 'approach', kind: 'action', before: first, after: attacking},
      {block_id: 'choice', kind: 'switch', before: attacking, after: attacking},
      {block_id: 'defense', kind: 'action', requires_timing: true, before: attacking, after: defended}
    ]
  };
  let now = 0;
  let hidden = false;
  const player = createExecutionTimelinePlayer({render() {}, showEvent() {}}, {
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

test('actions divide the configured duration and decisions take no extra time', async () => {
  const clock = timelineHarness();
  const playback = clock.player.play(clock.timeline);
  clock.frameAt(500);
  clock.frameAt(1000);
  expect(clock.timeline.unitDurationMs).toBe(500);
  expect(await playback).toEqual({completed: true, missedBlockId: null});
});

test('a hidden combat window is missed rather than replayed after return', async () => {
  const clock = timelineHarness();
  const playback = clock.player.play(clock.timeline);
  clock.frameAt(500, true);
  clock.frameAt(1200);
  expect(await playback).toEqual({completed: true, missedBlockId: 'defense'});
});

test('a frame stall can miss the defense window while visible too', async () => {
  const clock = timelineHarness();
  const playback = clock.player.play(clock.timeline);
  clock.frameAt(1200);
  expect(await playback).toEqual({completed: true, missedBlockId: 'defense'});
});

test('cancellation settles playback without completing the encounter', async () => {
  const clock = timelineHarness();
  const playback = clock.player.play(clock.timeline);
  clock.player.cancel();
  clock.frameAt(1200);
  expect(await playback).toEqual({completed: false, missedBlockId: null});
  expect(clock.player.isRunning()).toBe(false);
});
