import {
  registerValueAndAssignmentBlocks, valueAndAssignmentCategories
} from './value_and_assignment_blocks.js';
import {
  registerControlAndActionBlocks, controlAndActionCategories
} from './control_and_action_blocks.js';

// ===========================================================================
// Register the shared vocabulary once; encounters request blocks by stable ID
// ===========================================================================
export function registerBlockPool(Blockly, options = {}) {
  registerValueAndAssignmentBlocks(Blockly, options);
  registerControlAndActionBlocks(Blockly, options.workspacePolicy);
}

// ============================================================================
// Build a toolbox containing only the blocks requested by the active encounter
// ============================================================================
export function createToolboxFromRequests(Blockly, requestedTypes) {
  const categories = new Map();
  const definitions = valueAndAssignmentCategories.concat(controlAndActionCategories);

  for (const category of definitions) {
    const existing = categories.get(category.name);
    if (existing) {
      existing.blockTypes = existing.blockTypes.concat(category.blockTypes);
    } else {
      categories.set(category.name, {
        name: category.name,
        colour: category.colour,
        blockTypes: category.blockTypes.slice()
      });
    }
  }

  const categoryList = Array.from(categories.values());
  const knownTypes = new Set();
  for (const category of categoryList) {
    for (const type of category.blockTypes) knownTypes.add(type);
  }

  for (const type of requestedTypes) {
    if (!knownTypes.has(type) || !Blockly.Blocks[type]) {
      throw new Error(`The shared block pool does not define ${type}.`);
    }
  }

  const requested = new Set(requestedTypes);
  const contents = [];
  for (const category of categoryList) {
    const blocks = [];
    for (const type of category.blockTypes) {
      if (requested.has(type)) blocks.push({kind: 'block', type: type});
    }
    if (blocks.length > 0) {
      contents.push({
        kind: 'category',
        name: category.name,
        colour: category.colour,
        contents: blocks
      });
    }
  }

  return {kind: 'categoryToolbox', contents: contents};
}
