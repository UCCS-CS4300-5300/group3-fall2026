// ===========================================================================
// Define reusable actions and conditions; encounters request their own subset
// ===========================================================================

// The historical boss_ prefix is kept for saved programs; these definitions
// belong to the shared pool and can be requested by any encounter.
const actionBlocks = [
  ['make_noise', 'Attract an undetected zombie. Uses one action turn.'],
  ['wait', 'Let one action turn pass without moving or attacking.'],
  ['step_forward', 'Move closer to the zombie. Uses one action turn.'],
  ['hold_position', 'Stay in place while one action turn passes.'],
  ['dodge', 'Avoid a grab. Uses one action turn.'],
  ['block', 'Defend against a swipe. Uses one action turn.'],
  ['step_back', 'Avoid a lunge by stepping back. Uses one action turn.'],
  ['duck', 'Avoid a high swing. Uses one action turn.'],
  ['step_aside', 'Avoid a charge. Uses one action turn.'],
  ['attack', 'Finish the encounter after the correct defense. Uses one action turn.']
].map(([name, tooltip]) => ({
  type: `boss_${name}`,
  message0: `${name}()`,
  previousStatement: null,
  nextStatement: null,
  colour: 290,
  tooltip
}));

// These read current encounter state; evaluating a condition consumes no turns.
const conditionBlocks = [
  ['undetected', 'True when the zombie has not detected the player.'],
  ['not_close', 'True while the approach action units have not finished.']
].map(([name, tooltip]) => ({
  type: `boss_${name}`,
  message0: name,
  output: 'Boolean',
  colour: 210,
  tooltip
}));

// =============================================================
// Represent zombie attacks as values for the case label sockets
// =============================================================
const zombieActionBlocks = ['grab', 'swipe', 'lunge', 'high_swing', 'charge'].map(name => ({
  type: `boss_${name}`,
  message0: name.replaceAll('_', ' '),
  output: 'ZombieAction',
  colour: 20,
  tooltip: `Match the zombie's ${name.replaceAll('_', ' ')} attack in a case.`
}));

export const controlAndActionCategories = [
  {name: 'Logic', colour: '210', blockTypes: [
    'controls_if', 'controls_ifelse', 'boss_switch', 'boss_case', 'logic_operation'
  ]},
  {name: 'Conditions', colour: '210', blockTypes: conditionBlocks.map(({type}) => type)},
  {name: 'Zombie actions', colour: '20', blockTypes: zombieActionBlocks.map(({type}) => type)},
  {name: 'Actions', colour: '290', blockTypes: actionBlocks.map(({type}) => type)}
];

// =======================================================================
// Register pooled control blocks and enforce the structure of case chains
// =======================================================================
export function registerControlAndActionBlocks(Blockly, policy = {}) {
  Blockly.defineBlocksWithJsonArray(actionBlocks.concat(conditionBlocks, zombieActionBlocks));

  let expression = policy.switch_expression;
  if (expression === null || expression === undefined) expression = 'value';

  Blockly.defineBlocksWithJsonArray([{
    type: 'boss_switch',
    message0: 'switch %1 %2',
    args0: [
      {type: 'field_label_serializable', name: 'EXPRESSION', text: expression},
      {type: 'input_statement', name: 'CASES', check: 'CaseStatement'}
    ],
    previousStatement: null,
    nextStatement: null,
    colour: 210,
    tooltip: 'Run the matching case once, then leave the switch. Cases do not fall through.'
  }]);

  Blockly.Blocks.boss_case = {
    init() {
      this.appendValueInput('ATTACK').setCheck('ZombieAction').appendField('case');
      this.appendStatementInput('DO').appendField('do');
      this.setPreviousStatement(true, 'CaseStatement');
      this.setNextStatement(true, 'CaseStatement');
      this.setColour(210);
      this.setTooltip('Connect a zombie action to match, then place your response inside this case.');
    }
  };

  // An untyped Blockly statement otherwise connects to typed case inputs too.
  // Restrict the case chain without changing normal if/action connections.
  class CaseChainConnectionChecker extends Blockly.ConnectionChecker {
    doTypeChecks(a, b) {
      const statementConnection = a.type === Blockly.ConnectionType.PREVIOUS_STATEMENT
        || b.type === Blockly.ConnectionType.PREVIOUS_STATEMENT;
      if (!statementConnection) return super.doTypeChecks(a, b);

      const previous = a.type === Blockly.ConnectionType.PREVIOUS_STATEMENT ? a : b;
      const parentConnection = previous === a ? b : a;
      const child = previous.getSourceBlock();
      const parent = parentConnection.getSourceBlock();
      const caseSlot = (parent.type === 'boss_switch'
        && parent.getInput('CASES').connection === parentConnection)
        || (parent.type === 'boss_case' && parent.nextConnection === parentConnection);
      if (child.type === 'boss_case' || caseSlot) return child.type === 'boss_case' && caseSlot;
      return super.doTypeChecks(a, b);
    }
  }
  Blockly.registry.register(
    Blockly.registry.Type.CONNECTION_CHECKER, 'case_chain_connections', CaseChainConnectionChecker, true
  );
}
