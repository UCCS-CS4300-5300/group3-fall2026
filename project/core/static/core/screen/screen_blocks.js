// Block definitions control appearance and connections. The toolbox chooses
// which blocks are available, and the runner supplies their behavior.

// Zombie interaction blocks used by the existing punch lesson.
const zombieActionBlocks = [
  {
    type: 'screen_punch',
    message0: 'punch zombie',
    previousStatement: null,
    nextStatement: null,
    colour: 290
  },
  {
    type: 'screen_zombie',
    message0: 'zombie',
    output: 'Boolean',
    colour: 210
  }
];

// Shared logic and literal blocks: any lesson can include these in its toolbox.
const logicBlocks = [
  {
    type: 'logic_true',
    message0: 'true',
    output: 'Boolean',
    colour: 210
  },
  {
    type: 'logic_false',
    message0: 'false',
    output: 'Boolean',
    colour: 210
  },
  {
    type: 'math_integer',
    message0: '%1',
    args0: [{type: 'field_number', name: 'VALUE', value: 0, precision: 1}],
    output: 'Number',
    colour: 230
  }
];

// Variables boss lesson: assignments to this encounter's fixed variable names.
const bossVariableBlocks = [
  {
    type: 'screen_zombie_alive',
    message0: 'set zombie_alive to %1',
    args0: [{type: 'input_value', name: 'VALUE', check: 'Boolean'}],
    previousStatement: null,
    nextStatement: null,
    colour: 290
  },
  {
    type: 'screen_zombie_speed',
    message0: 'set zombie_speed to %1',
    args0: [{type: 'input_value', name: 'VALUE', check: 'Number'}],
    previousStatement: null,
    nextStatement: null,
    colour: 290
  }
];

// Register literal, punch, and boss assignment definitions on this Blockly
// instance. The toolbox separately chooses which types the player can use.
export function registerScreenBlocks(Blockly) {
  Blockly.defineBlocksWithJsonArray([
    ...logicBlocks,
    ...zombieActionBlocks,
    ...bossVariableBlocks
  ]);
}
