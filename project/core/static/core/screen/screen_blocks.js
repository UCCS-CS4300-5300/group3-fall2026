// Define block appearance and connections; the toolbox selects blocks and the runner executes them.

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
    message0: 'zombie_alive %1',
    args0: [{type: 'input_value', name: 'VALUE', check: 'Boolean'}],
    previousStatement: null,
    nextStatement: null,
    colour: 290
  },
  {
    type: 'screen_zombie_speed',
    message0: 'zombie_speed %1',
    args0: [{type: 'input_value', name: 'VALUE', check: 'Number'}],
    previousStatement: null,
    nextStatement: null,
    colour: 290
  }
];

// Corner Store jumpscare: one block per line of the cashier's register program; dropdowns hold the fixes.
const cashierBlocks = [
  {
    type: 'screen_cashier_cans',
    message0: 'cans = %1',
    args0: [{type: 'field_dropdown', name: 'VALUE', options: [['"6"', '"6"'], ['int("6")', 'int("6")'], ['6', '6']]}],
    previousStatement: null,
    nextStatement: null,
    colour: 20
  },
  {
    type: 'screen_cashier_price',
    message0: 'price = %1',
    args0: [{type: 'field_dropdown', name: 'VALUE', options: [['2.50', '2.50'], ['"2.50"', '"2.50"'], ['int(2.50)', 'int(2.50)']]}],
    previousStatement: null,
    nextStatement: null,
    colour: 20
  },
  {
    type: 'screen_cashier_total',
    message0: 'total = %1',
    args0: [{type: 'field_dropdown', name: 'VALUE', options: [['cans * price', 'cans * price'], ['cans + price', 'cans + price'], ['price - cans', 'price - cans']]}],
    previousStatement: null,
    nextStatement: null,
    colour: 20
  },
  {
    type: 'screen_cashier_print',
    message0: 'print("Total: $" + %1)',
    args0: [{type: 'field_dropdown', name: 'VALUE', options: [['total', 'total'], ['str(total)', 'str(total)'], ['int(total)', 'int(total)']]}],
    previousStatement: null,
    nextStatement: null,
    colour: 20
  }
];

// Register shared, punch, and boss blocks; the toolbox selects which types are available.
export function registerScreenBlocks(Blockly, {integerDefaultValue = 0, rejectZeroIntegers = false} = {}) {
  Blockly.defineBlocksWithJsonArray([
    ...logicBlocks,
    ...zombieActionBlocks,
    ...bossVariableBlocks,
    ...cashierBlocks
  ]);

  // Start integers at the lesson's default; rejecting zero keeps the field's previous valid value.
  const initializeIntegerBlock = Blockly.Blocks.math_integer.init;
  Blockly.Blocks.math_integer.init = function() {
    initializeIntegerBlock.call(this);
    this.setFieldValue(integerDefaultValue, 'VALUE');
    if (rejectZeroIntegers) {
      this.getField('VALUE').setValidator(value => value === 0 ? null : value);
    }
  };
}
