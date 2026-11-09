import {afterEach, beforeEach, expect, test} from 'vitest';
import {Blockly} from '../core/static/core/blockly/blockly_setup.js';
import {createToolboxFromRequests, registerBlockPool} from '../core/static/core/blockly/block_pool.js';
import {validateBlockAllowances, upgradeSavedBlockConnections} from '../core/static/core/blockly/workspace_policy.js';

registerBlockPool(Blockly);
const options = {plugins: {connectionChecker: 'case_chain_connections'}};
const limits = {controls_if: 3, boss_switch: 1, boss_case: 5};
let workspace;

beforeEach(() => {
  workspace = new Blockly.Workspace({plugins: options.plugins, maxInstances: limits});
  workspace.blockPolicy = {case_labels: ['grab', 'swipe', 'lunge', 'high_swing', 'charge']};
});
afterEach(() => workspace.dispose());

function legacyWorkspace() {
  return {blocks: {blocks: [{
      type: 'boss_switch', id: 'switch', fields: {CASE0: 'lunge'},
      inputs: {DO0: {block: {type: 'boss_step_back', id: 'defense'}}},
      next: {block: {
        type: 'controls_if', id: 'old-guard', inputs: {
          IF0: {block: {type: 'logic_operation', id: 'old-and', inputs: {
            A: {block: {type: 'boss_recovering', id: 'old-recovering'}},
            B: {block: {type: 'boss_close', id: 'old-close'}}
          }}},
          DO0: {block: {type: 'boss_attack', id: 'finish'}}
        }
      }}
    }]}};
}

test('the toolbox includes only requested pooled blocks', () => {
  const requested = ['controls_if', 'boss_switch', 'boss_grab', 'boss_swipe',
    'boss_lunge', 'boss_high_swing', 'boss_charge'];
  const toolbox = createToolboxFromRequests(Blockly, requested);
  expect(toolbox.contents.flatMap(category => category.contents.map(block => block.type)))
    .toEqual(requested);
  expect(toolbox.contents.map(category => category.name)).toEqual(['Logic', 'Zombie actions']);
});

test('case sockets accept zombie actions and reject Boolean conditions', () => {
  const socket = workspace.newBlock('boss_case').getInput('ATTACK').connection;
  expect(workspace.connectionChecker.canConnect(
    socket, workspace.newBlock('boss_lunge').outputConnection, false
  )).toBe(true);
  expect(workspace.connectionChecker.canConnect(
    socket, workspace.newBlock('boss_undetected').outputConnection, false
  )).toBe(false);
});

test('case chains exclude actions and ordinary branches exclude cases', () => {
  const choice = workspace.newBlock('boss_switch');
  const caseBlock = workspace.newBlock('boss_case');
  const action = workspace.newBlock('boss_step_back');
  const branch = workspace.newBlock('controls_if');
  expect(workspace.connectionChecker.canConnect(
    choice.getInput('CASES').connection, action.previousConnection, false
  )).toBe(false);
  expect(workspace.connectionChecker.canConnect(
    branch.getInput('DO0').connection, caseBlock.previousConnection, false
  )).toBe(false);
});

test('case labels and connected actions survive save and restore', () => {
  const choice = workspace.newBlock('boss_switch');
  const caseBlock = workspace.newBlock('boss_case');
  caseBlock.getInput('ATTACK').connection.connect(workspace.newBlock('boss_lunge').outputConnection);
  choice.getInput('CASES').connection.connect(caseBlock.previousConnection);
  caseBlock.getInput('DO').connection.connect(workspace.newBlock('boss_step_back').previousConnection);
  const saved = Blockly.serialization.workspaces.save(workspace);
  const restored = new Blockly.Workspace(options);
  try {
    Blockly.serialization.workspaces.load(saved, restored);
    expect(Blockly.serialization.workspaces.save(restored)).toEqual(saved);
    expect(restored.getBlockById(caseBlock.id).getInputTargetBlock('DO').type).toBe('boss_step_back');
  } finally {
    restored.dispose();
  }
});

test('legacy saves retain their five cases and finishing attack', () => {
  const migrated = upgradeSavedBlockConnections(legacyWorkspace(), Blockly);
  Blockly.serialization.workspaces.load(migrated, workspace);
  expect(workspace.getBlocksByType('boss_case', false)).toHaveLength(5);
  expect(workspace.getBlockById('switch').getNextBlock().id).toBe('finish');
});

test('saved text case labels become connected zombie action blocks', () => {
  const saved = {blocks: {blocks: [{type: 'boss_case', id: 'case', fields: {ATTACK: 'lunge'},
    inputs: {DO: {block: {type: 'boss_step_back', id: 'defense'}}}}]}};
  Blockly.serialization.workspaces.load(upgradeSavedBlockConnections(saved, Blockly), workspace);
  expect(workspace.getBlockById('case').getInputTargetBlock('ATTACK').type).toBe('boss_lunge');
  expect(workspace.getBlockById('case').getInputTargetBlock('DO').id).toBe('defense');
});

test('deleting a case restores its allowance', () => {
  for (let index = 0; index < 5; index++) workspace.newBlock('boss_case');
  expect(workspace.isCapacityAvailable({boss_case: 1})).toBe(false);
  workspace.getBlocksByType('boss_case', false).at(-1).dispose(true);
  expect(workspace.isCapacityAvailable({boss_case: 1})).toBe(true);
});

test('pre-run validation rejects excess if blocks', () => {
  for (let index = 0; index < 4; index++) workspace.newBlock('controls_if');
  expect(() => validateBlockAllowances(workspace, {limits: limits, allow_if_mutation: false}))
    .toThrow('Maximum: 3');
});
