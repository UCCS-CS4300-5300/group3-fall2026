// @vitest-environment jsdom
import {afterEach, beforeEach, expect, test, vi} from 'vitest';
import {createEncounterController} from '../core/static/core/boss/encounter_controller.js';

const workspace = vi.hoisted(() => ({
  collectProgram: vi.fn(() => ({mission_id: 2, room_id: 10, workspace: {}})),
  saveToForm: vi.fn(), resize: vi.fn(), destroy: vi.fn(), setLocked: vi.fn()
}));
const movement = vi.hoisted(() => ({
  isReady: vi.fn(() => true),
  onReady: vi.fn(listener => { listener(true); return vi.fn(); }),
  start: vi.fn(() => 1), applyResult: vi.fn(), fail: vi.fn(),
  reset: vi.fn(), destroy: vi.fn(), cancelExecution: vi.fn(),
  playExecution: vi.fn(async () => ({completed: true, missedBlockId: null}))
}));

vi.mock('../core/static/core/blockly/workspace_controller.js', () => ({
  createWorkspaceController: () => workspace
}));
vi.mock('@png-movement/png_move.js', () => ({initializeMovement: () => movement}));

const result = {playback_id: 'attempt', passed: true, feedback: 'Victory.', details: ['Action units: 5/5.']};
const response = {ok: true, json: async () => result};
let encounter;
let fetchRequest;

beforeEach(() => {
  vi.clearAllMocks();
  document.body.innerHTML = `
    <button id="lesson-run">Run</button><div id="screen-status"></div>
    <div id="screen-task" data-mission-id="2" data-room-id="10" data-check-url="/check/" data-csrf-token="token"></div>
    <form data-save-workspace><input name="workspace_json">
      <button class="boss-exit" data-complete-url="/finish/">Exit</button>
    </form>
    <script id="screen-workspace-config" type="application/json">{"playback":"timeline"}</script>
    <script id="screen-initial-variables" type="application/json">{"zombie_speed":10}</script>
    <script id="screen-movement-config" type="application/json">{}</script>`;
  fetchRequest = vi.fn().mockResolvedValue(response);
  vi.stubGlobal('fetch', fetchRequest);
  encounter = createEncounterController(document);
});

afterEach(() => {
  encounter.destroy();
  vi.unstubAllGlobals();
});

test('start collects the program and disables Run while submitting', async () => {
  let finishRequest;
  fetchRequest.mockImplementationOnce(() => new Promise(resolve => { finishRequest = resolve; }));
  const run = encounter.start();
  expect(document.getElementById('lesson-run').disabled).toBe(true);
  expect(JSON.parse(fetchRequest.mock.calls[0][1].body))
    .toEqual({mission_id: 2, room_id: 10, workspace: {}});
  finishRequest(response);
  await run;
});

test('reset aborts the request and ignores its late result', async () => {
  let finishRequest;
  fetchRequest.mockImplementationOnce(() => new Promise(resolve => { finishRequest = resolve; }));
  const run = encounter.start();
  encounter.reset();
  expect(fetchRequest.mock.calls[0][1].signal.aborted).toBe(true);
  finishRequest(response);
  await run;
  expect(document.getElementById('screen-status').textContent).toBe('');
});

test('a verified win displays feedback and unlocks Exit', async () => {
  await encounter.start();
  expect(document.getElementById('screen-status').textContent).toBe('Victory. Action units: 5/5.');
  expect(document.querySelector('.boss-exit').getAttribute('formaction')).toBe('/finish/');
});

test('timeline playback receives the execution record without starting continuous animation', async () => {
  await encounter.start();
  expect(movement.start).not.toHaveBeenCalled();
  expect(movement.playExecution).toHaveBeenCalledWith(result, expect.any(Function));
});

test('navigation saves the workspace and destruction releases it', () => {
  document.querySelector('form').dispatchEvent(new Event('submit', {cancelable: true}));
  expect(workspace.saveToForm).toHaveBeenCalledTimes(1);
  encounter.destroy();
  expect(workspace.destroy).toHaveBeenCalledTimes(1);
});

test('continuous playback starts at the initial speed and receives the result', async () => {
  encounter.destroy();
  document.getElementById('screen-workspace-config').textContent = '{"playback":"continuous"}';
  encounter = createEncounterController(document);
  await encounter.start();
  expect(movement.start).toHaveBeenCalledWith(10);
  expect(movement.applyResult).toHaveBeenCalledWith(1, result);
});

test('a pending timeline cannot unlock Exit before playback finishes', async () => {
  let finishPlayback;
  movement.playExecution.mockImplementationOnce(() => new Promise(resolve => { finishPlayback = resolve; }));
  const run = encounter.start();
  await vi.waitFor(() => { if (!finishPlayback) throw new Error('Playback has not started.'); });
  expect(document.getElementById('lesson-run').disabled).toBe(true);
  expect(document.querySelector('.boss-exit').hasAttribute('formaction')).toBe(false);
  finishPlayback({completed: true, missedBlockId: null});
  await run;
});
