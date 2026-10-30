import {afterEach, beforeEach, expect, test} from 'vitest';
import {MotionGlobalConfig, processFrame} from 'motion';
import {createTranslation, createRunAttempt} from '../png_move.js';

const activeTranslations = [];

beforeEach(() => {
  MotionGlobalConfig.useManualTiming = true;
  processFrame(0);
});

afterEach(() => {
  activeTranslations.splice(0).forEach(translation => translation.reset());
  processFrame(0);
  MotionGlobalConfig.useManualTiming = false;
});

// Advance the real Motion engine, rather than mocking its translation controls.
function clockHarness(settings = {}, durationMs = 1000) {
  const renders = [];
  const translation = createTranslation(durationMs,
    (elapsed, state) => renders.push({elapsed, state}), settings);
  activeTranslations.push(translation);

  async function frameAt(time) {
    processFrame(time);
    // Motion forwards completion callbacks through its finished promise.
    await Promise.resolve();
  }

  return {translation, renders, frameAt};
}

test('changing speed preserves position and applies the new rate', async () => {
  const clock = clockHarness();
  clock.translation.start();
  await clock.frameAt(200);
  clock.translation.setSpeed(20);
  await clock.frameAt(400);
  expect(clock.renders.at(-1).elapsed).toBe(600);
});

test.each([{speed: 0, expected: 20}, {speed: 100, expected: 400}])(
  'clamps movement speed $speed', async ({speed, expected}) => {
    const clock = clockHarness();
    clock.translation.start(speed);
    await clock.frameAt(200);
    expect(clock.renders.at(-1).elapsed).toBe(expected);
  }
);

test('an immediate success waits for 500 visible milliseconds before death', async () => {
  const clock = clockHarness({minimum_visible_ms: 500});
  clock.translation.start();
  clock.translation.die();
  await clock.frameAt(499);
  expect(clock.renders.at(-1).state).toBe('approaching');
});

test('death freezes the current pose at the visible-time threshold', async () => {
  const clock = clockHarness({minimum_visible_ms: 500});
  clock.translation.start();
  clock.translation.die();
  await clock.frameAt(500);
  await clock.frameAt(900);
  expect(clock.renders.at(-1)).toEqual({elapsed: 500, state: 'dead'});
});

test('hidden time does not satisfy the death visibility delay', async () => {
  const clock = clockHarness({minimum_visible_ms: 500});
  clock.translation.start();
  clock.translation.die();
  await clock.frameAt(200);
  clock.translation.pause();
  await clock.frameAt(10200);
  clock.translation.resume();
  await clock.frameAt(10499);
  expect(clock.renders.at(-1).state).toBe('approaching');
});

test('a short translation holds its endpoint until the visible death delay ends', async () => {
  const clock = clockHarness({minimum_visible_ms: 500}, 100);
  clock.translation.start();
  clock.translation.die();
  await clock.frameAt(200);
  await clock.frameAt(500);
  expect(clock.renders.at(-1)).toEqual({elapsed: 100, state: 'dead'});
});

test('a previous Run cannot kill a newer attempt', () => {
  const clock = clockHarness();
  const encounter = createRunAttempt(clock.translation, () => {});
  const previous = encounter.start();
  encounter.start();
  encounter.applyResult(previous, {passed: true});
  expect(clock.renders.at(-1).state).toBe('approaching');
});

test('Reset invalidates a pending success', () => {
  const clock = clockHarness();
  const encounter = createRunAttempt(clock.translation, () => {});
  const attempt = encounter.start();
  encounter.reset();
  encounter.applyResult(attempt, {passed: true});
  expect(clock.renders.at(-1).state).toBe('idle');
});

test('reset ignores completion callbacks already queued by Motion', async () => {
  const clock = clockHarness();
  clock.translation.start();
  processFrame(1000);
  clock.translation.reset();
  await clock.frameAt(1400);
  expect(clock.renders.at(-1)).toEqual({elapsed: 0, state: 'idle'});
});

test('replay cannot reuse the previous attempt visibility delay', async () => {
  const clock = clockHarness({minimum_visible_ms: 500});
  clock.translation.start();
  processFrame(600);
  clock.translation.start();
  clock.translation.die();
  await clock.frameAt(700);
  expect(clock.renders.at(-1).state).toBe('approaching');
});
