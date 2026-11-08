import {expect, test} from 'vitest';
import {Blockly} from '../core/static/core/blockly/blockly_setup.js';
import {registerPoliceBossBlocks} from '../core/static/core/boss/boss_blocks.js';

registerPoliceBossBlocks(Blockly);

test('make_noise fits inside Blockly if/else', () => {
  const workspace = new Blockly.Workspace();
  try {
    const branch = workspace.newBlock('controls_ifelse');
    const noise = workspace.newBlock('boss_make_noise');
    branch.getInput('DO0').connection.connect(noise.previousConnection);
    expect(branch.getInputTargetBlock('DO0')).toBe(noise);
  } finally {
    workspace.dispose();
  }
});



