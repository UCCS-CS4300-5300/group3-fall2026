import {afterEach, beforeEach, expect, test} from 'vitest';
import {Blockly} from '../core/static/core/blockly/blockly_setup.js';
import {registerScreenBlocks} from '../core/static/core/screen/screen_blocks.js';

registerScreenBlocks(Blockly, {integerDefaultValue: 10, rejectZeroIntegers: true});
let workspace;

beforeEach(() => { workspace = new Blockly.Workspace(); });
afterEach(() => { workspace.dispose(); });

test.each([10, 3])('entering zero keeps the previous valid integer %i', previousValue => {
  const integer = workspace.newBlock('math_integer');
  integer.setFieldValue(previousValue, 'VALUE');
  integer.setFieldValue(0, 'VALUE');
  expect(integer.getFieldValue('VALUE')).toBe(previousValue);
});

test('restoring a saved zero uses the starting speed', () => {
  const integer = Blockly.serialization.blocks.append({
    type: 'math_integer', fields: {VALUE: 0}
  }, workspace);
  expect(integer.getFieldValue('VALUE')).toBe(10);
});
