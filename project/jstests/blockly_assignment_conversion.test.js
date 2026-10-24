import {afterEach, beforeEach, expect, test} from 'vitest';
import {Blockly} from '../core/static/core/blockly/blockly_setup.js';
import {registerScreenBlocks} from '../core/static/core/screen/screen_blocks.js';
import {convertWorkspaceBlocksToAssignments} from '../core/static/core/screen/blockly_assignments.js';

registerScreenBlocks(Blockly);
let workspace;

beforeEach(() => { workspace = new Blockly.Workspace(); });
afterEach(() => { workspace.dispose(); });

test('shared integer blocks allow zero when the lesson does not restrict it', () => {
  const integer = workspace.newBlock('math_integer');
  integer.setFieldValue(3, 'VALUE');
  integer.setFieldValue(0, 'VALUE');
  expect(integer.getFieldValue('VALUE')).toBe(0);
});

// Given two registered Blockly type IDs, create both blocks, connect the literal
// to the assignment's VALUE socket, and return the assignment block for the test.
function createAssignmentWithLiteral(assignmentType, valueType) {
  const assignment = workspace.newBlock(assignmentType);
  const value = workspace.newBlock(valueType);
  assignment.getInput('VALUE').connection.connect(value.outputConnection);
  return assignment;
}

test('converts connected assignments in execution order', () => {
  const speed = createAssignmentWithLiteral('screen_zombie_speed', 'math_integer');
  speed.getInputTargetBlock('VALUE').setFieldValue(3, 'VALUE');
  const alive = createAssignmentWithLiteral('screen_zombie_alive', 'logic_false');
  speed.nextConnection.connect(alive.previousConnection);
  expect(convertWorkspaceBlocksToAssignments(workspace)).toEqual([
    {variable: 'zombie_speed', value: 3},
    {variable: 'zombie_alive', value: false}
  ]);
});

test('reads edited values each time the program is built', () => {
  const speed = createAssignmentWithLiteral('screen_zombie_speed', 'math_integer');
  speed.getInputTargetBlock('VALUE').setFieldValue(3, 'VALUE');
  expect(convertWorkspaceBlocksToAssignments(workspace)[0].value).toBe(3);
  speed.getInputTargetBlock('VALUE').setFieldValue(7, 'VALUE');
  expect(convertWorkspaceBlocksToAssignments(workspace)[0].value).toBe(7);
});

test('reports an empty assignment socket', () => {
  workspace.newBlock('screen_zombie_speed');
  expect(() => convertWorkspaceBlocksToAssignments(workspace)).toThrow('Connect a value');
});
