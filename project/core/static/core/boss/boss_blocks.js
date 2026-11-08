// Police Station boss blocks. Their encounter effects are implemented in Stage 3.
export function registerPoliceBossBlocks(Blockly) {
  Blockly.defineBlocksWithJsonArray([{
    type: 'boss_make_noise',
    message0: 'make_noise()',
    previousStatement: null,
    nextStatement: null,
    colour: 290,
    tooltip: 'When executed, sets user_found to true.'
  }]);
}
