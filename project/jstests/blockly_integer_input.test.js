import {afterEach, beforeEach, expect, test} from 'vitest';
import {Blockly} from '../core/static/core/blockly/blockly_setup.js';
import {registerScreenBlocks} from '../core/static/core/screen/screen_blocks.js';

registerScreenBlocks(Blockly, {integerDefaultValue: 10, rejectZeroIntegers: true});
let workspace;

beforeEach(() => { workspace = new Blockly.Workspace(); });
afterEach(() => { workspace.dispose(); });

test('new boss integers start at the zombie speed of ten', () => {
  const integer = workspace.newBlock('math_integer');
  expect(integer.getFieldValue('VALUE')).toBe(10);
});

test('typing zero keeps the previous valid speed', () => {
  const integer = workspace.newBlock('math_integer');
  integer.setFieldValue(3, 'VALUE');
  integer.setFieldValue('0', 'VALUE');
  expect(integer.getFieldValue('VALUE')).toBe(3);
});

test('restoring a saved zero uses the starting speed', () => {
  const integer = Blockly.serialization.blocks.append({
    type: 'math_integer', fields: {VALUE: 0}
  }, workspace);
  expect(integer.getFieldValue('VALUE')).toBe(10);
});

test('boss integers accept the minimum speed of one', () => {
  const integer = workspace.newBlock('math_integer');
  integer.setFieldValue(1, 'VALUE');
  expect(integer.getFieldValue('VALUE')).toBe(1);
});
