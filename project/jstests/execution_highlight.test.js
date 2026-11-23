// @vitest-environment jsdom
import {expect, test, vi} from 'vitest';
import {createExecutionHighlighter} from '../core/static/core/blockly/execution_highlight.js';
import {buildExecutionTimeline, createExecutionTimelinePlayer}
  from '../core/static/core/png_movement/execution_timeline.js';

function createFixture() {
  // SVG groups model Blockly's public getSvgRoot() boundary without depending
  // on its renderer's measurements, which jsdom does not implement.
  const roots = new Map(['first', 'second', 'condition'].map(id => [
    id, document.createElementNS('http://www.w3.org/2000/svg', 'g')
  ]));
  const workspace = {
    getBlockById: id => roots.has(id) ? {getSvgRoot: () => roots.get(id)} : null,
    highlightBlock: vi.fn()
  };
  return {roots, workspace, highlight: createExecutionHighlighter(workspace)};
}

test('action decoration transfers between executed block IDs and clears at the end', () => {
  const {roots, workspace, highlight} = createFixture();
  highlight.showStep({block_id: 'first', kind: 'action'}, 'start');
  expect(roots.get('first').classList.contains('boss-execution-action')).toBe(true);
  expect(workspace.highlightBlock).toHaveBeenLastCalledWith('first');

  highlight.showStep({block_id: 'second', kind: 'action'}, 'start');
  expect(roots.get('first').classList.length).toBe(0);
  expect(roots.get('second').classList.contains('boss-execution-action')).toBe(true);

  // A late end boundary cannot erase the newer active action.
  highlight.showStep({block_id: 'first'}, 'end');
  expect(roots.get('second').classList.contains('boss-execution-action')).toBe(true);
  highlight.showStep({block_id: 'second'}, 'end');
  expect(roots.get('second').classList.length).toBe(0);
  expect(workspace.highlightBlock).toHaveBeenLastCalledWith(null);
});

test('decisions use a separate class and missing blocks never retain a previous glow', () => {
  const {roots, highlight} = createFixture();
  highlight.showStep({block_id: 'condition', kind: 'condition'}, 'start');
  expect(roots.get('condition').classList.contains('boss-execution-decision')).toBe(true);
  expect(roots.get('condition').classList.contains('boss-execution-action')).toBe(false);

  highlight.showStep({block_id: 'deleted-block', kind: 'action'}, 'start');
  expect(roots.get('condition').classList.length).toBe(0);
  expect(() => { highlight.clear(); highlight.clear(); }).not.toThrow();
});

test('if, switch, and case containers do not steal the condition highlight', () => {
  const {roots, workspace, highlight} = createFixture();
  highlight.showStep({block_id: 'condition', kind: 'condition'}, 'start');
  workspace.highlightBlock.mockClear();

  for (const kind of ['if', 'switch', 'case']) {
    highlight.showStep({block_id: 'first', kind}, 'start');
    highlight.showStep({block_id: 'first', kind}, 'end');
  }

  expect(roots.get('first').classList.length).toBe(0);
  expect(roots.get('condition').classList.contains('boss-execution-decision')).toBe(true);
  expect(workspace.highlightBlock).not.toHaveBeenCalled();
});

test('playback shows a softer conditional glow between two bright action slots', async () => {
  const {roots, highlight} = createFixture();
  const first = {turn: 0, progress: 0, phase: 'approaching'};
  const middle = {turn: 1, progress: 0.5, phase: 'approaching'};
  const last = {turn: 2, progress: 1, phase: 'defeated'};
  const timeline = buildExecutionTimeline({
    state: {action_units: 2},
    events: [
      {block_id: 'first', kind: 'action', before: first, after: middle},
      {block_id: 'condition', kind: 'condition', before: middle, after: middle},
      {block_id: 'second', kind: 'action', before: middle, after: last}
    ]
  }, 1000);
  let now = 0;
  const player = createExecutionTimelinePlayer({
    render() {},
    showEvent(event, _state, boundary) { highlight.showStep(event, boundary); }
  }, {
    now: () => now, isHidden: () => false,
    requestFrame: () => 1, cancelFrame() {}
  });
  const playback = player.play(timeline);
  expect(roots.get('first').classList.contains('boss-execution-action')).toBe(true);
  now = 600;
  player.refresh();
  expect(roots.get('first').classList.length).toBe(0);
  expect(roots.get('condition').classList.contains('boss-execution-decision')).toBe(true);
  expect(roots.get('second').classList.length).toBe(0);
  now = 625;
  player.refresh();
  expect(roots.get('condition').classList.length).toBe(0);
  expect(roots.get('second').classList.contains('boss-execution-action')).toBe(true);
  now = 1000;
  player.refresh();
  await playback;
  expect(roots.get('second').classList.length).toBe(0);
});
