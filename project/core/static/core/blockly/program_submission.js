import {convertWorkspaceBlocksToAssignments} from './assignment_conversion.js';
import {validateBlockAllowances} from './workspace_policy.js';

// =========================================================================
// Convert a workspace into the submission format requested by its encounter
// =========================================================================
export function createProgramSubmission(Blockly, workspace, roomIds, policy) {
  validateBlockAllowances(workspace, policy);

  const missionId = Number(roomIds.missionId);
  const roomId = Number(roomIds.roomId);

  switch (policy.submission_format) {
    case 'workspace': {
      const saved = Blockly.serialization.workspaces.save(workspace);

      // Blockly's ordered roots match its code-generation traversal: top to
      // bottom with its own LTR/RTL bias. Keep serialized children/connections
      // intact; only reorder the roots so the server receives execution order,
      // rather than block creation order. Saving for navigation is unaffected.
      if (saved.blocks) {
        const rootsById = new Map(saved.blocks.blocks.map(block => [block.id, block]));
        saved.blocks.blocks = workspace.getTopBlocks(true)
          .map(block => rootsById.get(block.id))
          .filter(block => block !== undefined);
      }

      return {
        mission_id: missionId,
        room_id: roomId,
        workspace: saved
      };
    }
    case 'assignments':
      // Send the variable/value assignments expected by assignment lessons.
      return {
        mission_id: missionId,
        room_id: roomId,
        assignments: convertWorkspaceBlocksToAssignments(workspace)
      };
    case 'punch':
      // Keep the text format used by the original punch checker.
      return {program: workspace.getTopBlocks(true).map(block => describePunchStatements(block)).join('')};
    default:
      throw new Error('This encounter requests an unsupported submission format.');
  }
}

// =================================================================
// Preserve the original punch lesson's indented-text program format
// =================================================================
function describePunchStatements(block, indent = '') {
  let program = '';

  for (; block; block = block.getNextBlock()) {
    if (block.type === 'screen_punch') {
      program += `${indent}punch zombie\n`;
    } else if (block.type === 'controls_if') {
      const condition = block.getInputTargetBlock('IF0');
      program += `${indent}if ${condition ? 'zombie' : '(empty)'}\n`;
      program += describePunchStatements(block.getInputTargetBlock('DO0'), indent + '  ');
    }
  }

  return program;
}
