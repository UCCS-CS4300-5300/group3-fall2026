// @vitest-environment jsdom
import {expect, test, vi} from 'vitest';
import {MotionGlobalConfig, processFrame} from 'motion';
import {initializeMovement} from '../png_move.js';

test('success rotates the rendered sprite eighty degrees without moving its feet', async () => {
  const floor = {
    matrix: [1, 0, 0, 0, 1, 0, 0, 0, 1],
    motion: {start_floor: [0.5, 0.5], end_floor: [0.5, 0.9],
      duration_ms: 2500, end_height: 0.45, end_depth: 1, foot_anchor: [0.5, 0.94]}
  };
  document.body.innerHTML = `<img class="room-background"><img id="png-move-sprite">
    <button id="png-preview"></button><button id="png-preview-reset"></button>
    <p id="png-preview-status"></p><script id="screen-floor-config"></script>
    <script id="screen-movement-config"></script>`;
  document.querySelector('#screen-floor-config').textContent = JSON.stringify(floor);
  document.querySelector('#screen-movement-config').textContent = JSON.stringify({
    enabled: true, minimum_visible_ms: 500, death_rotation_degrees: 80, normal_speed: 10
  });
  const sprite = document.querySelector('#png-move-sprite');
  for (const image of document.querySelectorAll('img')) {
    Object.defineProperties(image, {complete: {value: true}, naturalWidth: {value: 1000},
      naturalHeight: {value: 500}});
    image.getBoundingClientRect = () => ({width: 1000, height: 500});
  }
  Object.defineProperty(document, 'hidden', {value: false, configurable: true});
  vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
  const previousTiming = MotionGlobalConfig.useManualTiming;
  MotionGlobalConfig.useManualTiming = true;
  processFrame(0);
  const movement = initializeMovement();
  try {
    const attempt = movement.start();
    processFrame(600);
    await Promise.resolve();
    await Promise.resolve();
    const before = sprite.style.transform;
    movement.applyResult(attempt, {passed: true});
    expect(sprite.style.transform).toBe(before.replace('rotate(0deg)', 'rotate(80deg)'));
  } finally {
    movement.destroy();
    processFrame(600);
    MotionGlobalConfig.useManualTiming = previousTiming;
    vi.unstubAllGlobals();
    delete document.hidden;
  }
});
