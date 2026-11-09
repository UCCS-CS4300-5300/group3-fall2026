import {Blockly} from './blockly_setup.js';
import {registerBlockPool, createToolboxFromRequests} from './block_pool.js';
import {configureWorkspacePolicy, upgradeSavedBlockConnections} from './workspace_policy.js';
import {createProgramSubmission} from './program_submission.js';

// ==========================================================================
// Own the custom workspace, its saved connections, and its submission format
// ==========================================================================
export function createWorkspaceController(root, policy, initialVariables, movementSettings) {
  const workspaceElement = root.getElementById('blockly-workspace');
  let integerDefaultValue = initialVariables.zombie_speed;
  if (integerDefaultValue === null || integerDefaultValue === undefined) integerDefaultValue = 0;

  registerBlockPool(Blockly, {
    workspacePolicy: policy,
    integerDefaultValue: integerDefaultValue,
    integerBounds: Object.hasOwn(initialVariables, 'zombie_speed') ? movementSettings : null
  });

  const workspace = Blockly.inject(workspaceElement, {
    toolbox: createToolboxFromRequests(Blockly, policy.requested_blocks),
    maxInstances: policy.limits,
    plugins: {connectionChecker: 'case_chain_connections'},
    trashcan: true,
    zoom: {controls: true, wheel: true, startScale: 1.1},
    move: {scrollbars: true, drag: true, wheel: true}
  });

  configureWorkspacePolicy(workspace, policy, root.getElementById('block-allowances'));
  const savedState = JSON.parse(root.getElementById('screen-workspace-state').textContent);
  Blockly.serialization.workspaces.load(upgradeSavedBlockConnections(savedState, Blockly), workspace);

  function collectProgram(roomIds) {
    return createProgramSubmission(Blockly, workspace, roomIds, policy);
  }

  function saveToForm(form) {
    form.elements.namedItem('workspace_json').value = JSON.stringify(
      Blockly.serialization.workspaces.save(workspace)
    );
  }

  function resize() {
    Blockly.svgResize(workspace);
  }

  // =====================================================================
  // Close edit popups and prevent changes while the recorded attempt runs
  // =====================================================================
  function setLocked(locked) {
    if (locked) Blockly.hideChaff();
    workspaceElement.inert = locked;
  }

  function destroy() {
    workspace.dispose();
  }

  return {
    collectProgram: collectProgram,
    saveToForm: saveToForm,
    resize: resize,
    setLocked: setLocked,
    destroy: destroy
  };
}
