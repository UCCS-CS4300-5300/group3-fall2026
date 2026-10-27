// Lesson-specific assignment blocks map to the variables they write.
const assignmentBlockVariables = {
  screen_zombie_alive: 'zombie_alive',
  screen_zombie_speed: 'zombie_speed',
  screen_cashier_cans: 'cans',
  screen_cashier_price: 'price',
  screen_cashier_total: 'total',
  screen_cashier_print: 'print'
};

// Cashier blocks hold their value in a dropdown; other assignment blocks need a connected literal.
function getAssignmentValue(block) {
  if (block.getField('VALUE')) return block.getFieldValue('VALUE');
  return getLiteralBlockValue(block.getInputTargetBlock('VALUE'));
}

// Read a literal block as a boolean or integer; reject missing, disabled, or unsupported blocks.
function getLiteralBlockValue(block) {
  if (!block || !block.isEnabled()) {
    throw new Error('Connect a value to each assignment before running.');
  }
  if (block.type === 'logic_true') return true;
  if (block.type === 'logic_false') return false;
  if (block.type === 'math_integer') {
    const value = block.getFieldValue('VALUE');
    if (Number.isInteger(value)) return value;
  }
  throw new Error('Use a true, false, or integer block for the assignment value.');
}

// Convert enabled workspace assignment stacks into ordered {variable, value} records, ignoring loose literals.
export function convertWorkspaceBlocksToAssignments(workspace) {
  const assignments = [];
  for (const topBlock of workspace.getTopBlocks(true)) {
    // Loose value blocks do not perform assignments.
    if (topBlock.outputConnection) continue;
    for (let block = topBlock; block; block = block.getNextBlock()) {
      if (!block.isEnabled()) continue;
      if (!Object.hasOwn(assignmentBlockVariables, block.type)) {
        throw new Error('This program contains an unsupported assignment block.');
      }
      const variable = assignmentBlockVariables[block.type];
      const value = getAssignmentValue(block);
      assignments.push({variable, value});
    }
  }
  return assignments;
}
