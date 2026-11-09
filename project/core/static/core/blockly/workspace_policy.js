// =========================================================================
// Upgrade saved connections while preserving the player's remaining program
// =========================================================================
// Only the obsolete finishing guard is unwrapped. Other incomplete inputs stay
// visible for the player to repair.
export function upgradeSavedBlockConnections(saved, Blockly) {
  const state = structuredClone(saved);
  const retired = new Set(['boss_close', 'boss_recovering']);

  // Replace saved text labels with real value blocks, preserving case bodies.
  function upgradeCaseLabel(block) {
    if (block.type !== 'boss_case' || !block.fields) return;
    const label = block.fields.ATTACK;
    if (label === undefined) return;
    if (!block.inputs) block.inputs = {};
    if (!block.inputs.ATTACK && ['grab', 'swipe', 'lunge', 'high_swing', 'charge'].includes(label)) {
      block.inputs.ATTACK = {block: {
        type: `boss_${label}`, id: Blockly.utils.idGenerator.genUid()
      }};
    }
    delete block.fields.ATTACK;
  }

  function convert(block) {
    if (!block || retired.has(block.type)) return null;

    const condition = getConnectedInput(block, 'IF0');
    const left = getConnectedInput(condition, 'A');
    const right = getConnectedInput(condition, 'B');
    const action = getConnectedInput(block, 'DO0');
    const oldGuard = block.type === 'controls_if' && condition
      && condition.type === 'logic_operation'
      && (!condition.fields || condition.fields.OP !== 'OR')
      && left && right && retired.has(left.type) && retired.has(right.type)
      && action && action.type === 'boss_attack';

    if (block.next) {
      const next = convert(block.next.block);
      if (next) block.next = {block: next};
      else delete block.next;
    }

    if (oldGuard) {
      const attack = convert(action);
      let last = attack;
      while (last.next) last = last.next.block;
      if (block.next) last.next = block.next;
      return attack;
    }

    const inputs = block.inputs || {};
    for (const name of Object.keys(inputs)) {
      const child = convert(inputs[name].block);
      if (child) inputs[name] = {block: child};
      else delete inputs[name];
    }

    const fields = block.fields || {};
    const oldSwitch = Object.keys(fields).some(name => /^CASE[0-9]+$/.test(name))
      || Object.keys(inputs).some(name => /^DO[0-9]+$/.test(name));
    if (block.type === 'boss_switch' && oldSwitch) {
      const cases = [];
      for (let index = 0; index < 5; index++) {
        let label = fields[`CASE${index}`];
        if (label === null || label === undefined) label = '';

        const caseBlock = {
          type: 'boss_case',
          id: Blockly.utils.idGenerator.genUid(),
          fields: {ATTACK: label},
          inputs: {}
        };
        if (inputs[`DO${index}`]) caseBlock.inputs.DO = inputs[`DO${index}`];
        upgradeCaseLabel(caseBlock);
        if (index > 0) cases[index - 1].next = {block: caseBlock};
        cases.push(caseBlock);
      }
      block.fields = {};
      block.inputs = {CASES: {block: cases[0]}};
    }

    upgradeCaseLabel(block);
    return block;
  }

  if (state.blocks && state.blocks.blocks) {
    state.blocks.blocks = state.blocks.blocks.map(convert).filter(Boolean);
  }
  return state;
}

function getConnectedInput(block, name) {
  if (!block || !block.inputs || !block.inputs[name]) return null;
  return block.inputs[name].block;
}

// =====================================================================
// Check every placed block against the encounter's requested allowances
// =====================================================================
export function validateBlockAllowances(workspace, policy) {
  const limits = policy.limits || {};
  const counts = {};
  for (const type of Object.keys(limits)) {
    counts[type] = workspace.getBlocksByType(type, false).length;
    if (counts[type] > limits[type]) {
      throw new Error(`Too many ${describeBlockType(type)} blocks. Maximum: ${limits[type]}.`);
    }
  }

  if (policy.allow_if_mutation === false) {
    const plainIfBlocks = workspace.getBlocksByType('controls_if', false);
    for (const block of plainIfBlocks) {
      if (block.getInput('IF1') || block.getInput('ELSE')) {
        throw new Error('Use the supplied plain if and if/else blocks without extra branches.');
      }
    }
  }

  return counts;
}

function describeBlockType(type) {
  const names = {
    controls_if: 'if',
    controls_ifelse: 'if/else',
    boss_switch: 'switch',
    boss_case: 'case'
  };
  if (Object.hasOwn(names, type)) return names[type];
  return type.replace('boss_', '');
}

// ============================================================================
// Apply label choices, prevent extra if branches, and display allowance counts
// ============================================================================
export function configureWorkspacePolicy(workspace, policy, container) {
  workspace.blockPolicy = policy;
  const limits = policy.limits || {};

  const updateCounts = () => {
    // Hide the mutator so extra branches cannot bypass the if allowance.
    if (policy.allow_if_mutation === false) {
      for (const block of workspace.getBlocksByType('controls_if', false)) {
        if (typeof block.setMutator === 'function') block.setMutator(null);
      }
    }
    if (!container) return;

    const allowances = [];
    for (const type of Object.keys(limits)) {
      const maximum = limits[type];
      const used = workspace.getBlocksByType(type, false).length;
      allowances.push(`${describeBlockType(type)}: ${used}/${maximum}`);
    }
    container.textContent = allowances.join(', ');
  };
  workspace.addChangeListener(event => {
    if (!event.isUiEvent) updateCounts();
  });
  updateCounts();
}
