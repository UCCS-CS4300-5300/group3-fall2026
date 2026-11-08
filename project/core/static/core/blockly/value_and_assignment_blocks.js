// ===============================================================================
// Define pooled values and assignments without deciding which encounter uses them
// ===============================================================================

// ======================================================
// Provide the existing punch action and zombie condition
// ======================================================
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

// ==================================
// Provide Boolean and integer values
// ==================================
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

// =====================================================
// Provide assignments to the supported zombie variables
// =====================================================
const zombieVariableAssignments = [
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

// =============================================================
// Provide register-program lines with editable dropdown choices
// =============================================================
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

export const valueAndAssignmentCategories = [
  {name: 'Logic', colour: '210', blockTypes: ['logic_true', 'logic_false']},
  {name: 'Math', colour: '230', blockTypes: ['math_integer']},
  {name: 'Variables', colour: '290', blockTypes: zombieVariableAssignments.map(({type}) => type)},
  {name: 'Game', colour: '290', blockTypes: zombieActionBlocks.map(({type}) => type)},
  {name: 'Register', colour: '20', blockTypes: cashierBlocks.map(({type}) => type)}
];

// ==============================================================================
// Register definitions and configure integer values for the requesting workspace
// ==============================================================================
export function registerValueAndAssignmentBlocks(Blockly, {
  integerDefaultValue = 0, integerBounds = null
} = {}) {
  const definitions = logicBlocks.concat(
    zombieActionBlocks, zombieVariableAssignments, cashierBlocks
  );
  Blockly.defineBlocksWithJsonArray(definitions);

  // Requested speed literals use the same bounds as the server and movement clock.
  const initializeIntegerBlock = Blockly.Blocks.math_integer.init;
  Blockly.Blocks.math_integer.init = function() {
    initializeIntegerBlock.call(this);
    this.setFieldValue(integerDefaultValue, 'VALUE');
    if (integerBounds) {
      this.getField('VALUE').setValidator(value => (
        Math.min(integerBounds.speed_max, Math.max(integerBounds.speed_min, value))
      ));
    }
  };
}
