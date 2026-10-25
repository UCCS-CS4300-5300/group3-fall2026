import {afterEach, beforeEach, expect, test} from 'vitest';
import {Blockly} from '../core/static/core/blockly/blockly_setup.js';
import {registerScreenBlocks} from '../core/static/core/screen/screen_blocks.js';
import {convertWorkspaceBlocksToAssignments} from '../core/static/core/screen/blockly_assignments.js';

registerScreenBlocks(Blockly);
let workspace;

beforeEach(() => { workspace = new Blockly.Workspace(); });
afterEach(() => { workspace.dispose(); });

test('shared integer blocks still allow zero', () => {
  const integer = workspace.newBlock('math_integer');
  integer.setFieldValue(3, 'VALUE');
  integer.setFieldValue(0, 'VALUE');
  expect(integer.getFieldValue('VALUE')).toBe(0);
});

test('converts a connected false block to an alive assignment', () => {
  const assignment = workspace.newBlock('screen_zombie_alive');
  const literal = workspace.newBlock('logic_false');
  assignment.getInput('VALUE').connection.connect(literal.outputConnection);
  expect(convertWorkspaceBlocksToAssignments(workspace)).toEqual([
    {variable: 'zombie_alive', value: false}
  ]);
});

test('reads the edited integer when converting a speed assignment', () => {
  const assignment = workspace.newBlock('screen_zombie_speed');
  const integer = workspace.newBlock('math_integer');
  assignment.getInput('VALUE').connection.connect(integer.outputConnection);
  integer.setFieldValue(7, 'VALUE');
  expect(convertWorkspaceBlocksToAssignments(workspace)).toEqual([
    {variable: 'zombie_speed', value: 7}
  ]);
});

test('reports an assignment with no connected value', () => {
  workspace.newBlock('screen_zombie_speed');
  expect(() => convertWorkspaceBlocksToAssignments(workspace)).toThrow('Connect a value');
});

test('ignores loose literal blocks', () => {
  workspace.newBlock('logic_true');
  workspace.newBlock('math_integer');
  expect(convertWorkspaceBlocksToAssignments(workspace)).toEqual([]);
});

test('keeps chained assignments in execution order', () => {
  const first = workspace.newBlock('screen_zombie_alive');
  const second = workspace.newBlock('screen_zombie_alive');
  first.getInput('VALUE').connection.connect(workspace.newBlock('logic_true').outputConnection);
  second.getInput('VALUE').connection.connect(workspace.newBlock('logic_false').outputConnection);
  first.nextConnection.connect(second.previousConnection);
  const assignments = convertWorkspaceBlocksToAssignments(workspace);
  expect(assignments.map(assignment => assignment.value)).toEqual([true, false]);
});
