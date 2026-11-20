import {afterEach, beforeEach, expect, test} from 'vitest';
import {Blockly} from '../core/static/core/blockly/blockly_setup.js';
import {registerBlockPool} from '../core/static/core/blockly/block_pool.js';
import {createProgramSubmission} from '../core/static/core/blockly/program_submission.js';

registerBlockPool(Blockly);
let workspace;

beforeEach(() => { workspace = new Blockly.Workspace(); });
afterEach(() => { workspace.dispose(); });

function submit() {
  return createProgramSubmission(Blockly, workspace,
    {missionId: '2', roomId: '10'}, {submission_format: 'workspace'}).workspace;
}

test('disconnected stacks are submitted in Blockly order, not creation order', () => {
  const last = workspace.newBlock('boss_attack', 'last');
  last.moveBy(0, 300);
  const first = workspace.newBlock('boss_make_noise', 'first');
  first.moveBy(0, 20);
  const middle = workspace.newBlock('boss_wait', 'middle');
  middle.moveBy(0, 150);
  const orderedIds = () => workspace.getTopBlocks(true).map(block => block.id);

  expect(orderedIds()).toEqual(['first', 'middle', 'last']);
  expect(submit().blocks.blocks.map(block => block.id)).toEqual(orderedIds());

  last.moveBy(0, -300);
  expect(orderedIds()).toEqual(['last', 'first', 'middle']);
  expect(submit().blocks.blocks.map(block => block.id)).toEqual(orderedIds());
});

test('ordering roots preserves their connected statement chains and block IDs', () => {
  const separate = workspace.newBlock('boss_attack', 'separate');
  separate.moveBy(0, 300);
  const root = workspace.newBlock('boss_make_noise', 'root');
  const child = workspace.newBlock('boss_wait', 'child');
  root.nextConnection.connect(child.previousConnection);

  const saved = submit();
  expect(saved.blocks.blocks.map(block => block.id)).toEqual(['root', 'separate']);
  expect(saved.blocks.blocks[0].next.block.id).toBe('child');
});
