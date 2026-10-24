import {Blockly} from '../blockly/blockly_setup.js';
import {registerScreenBlocks} from './screen_blocks.js';
import {convertWorkspaceBlocksToAssignments} from './blockly_assignments.js';

const workspaceElement = document.getElementById('blockly-workspace');
const runButton = document.getElementById('lesson-run');
const resetButton = document.getElementById('lesson-reset');

console.info('[screen] Blockly module evaluated', {
  workspaceFound: Boolean(workspaceElement)
});


registerScreenBlocks(Blockly);

const lessonBlockTypes = JSON.parse(
  document.getElementById('screen-available-blocks').textContent
);

const workspace = Blockly.inject('blockly-workspace', {
  // Rooms without a LessonID keep the existing toolbox.
  toolbox: lessonBlockTypes === null ? {
    kind: 'categoryToolbox',
    contents: [
      {
        kind: 'category',
        name: 'Game',
        colour: '290',
        contents: [
          {kind: 'block', type: 'screen_punch'},
          {kind: 'block', type: 'screen_zombie'},
        ]
      },
      {
        kind: 'category',
        name: 'Logic',
        colour: '210',
        contents: [
          {kind: 'block', type: 'controls_if'}
      ]
      }
    ]
  } : {
    kind: 'flyoutToolbox',
    contents: lessonBlockTypes.map(type => ({kind: 'block', type}))
  },
  trashcan: true,
  zoom: {controls: true, wheel: true, startScale: 1.1},
  move: {scrollbars: true, drag: true, wheel: true}
});
console.info('[screen] Blockly workspace injected', workspace);

const savedWorkspace = document.getElementById('screen-workspace-state');
Blockly.serialization.workspaces.load(JSON.parse(savedWorkspace.textContent), workspace);

document.querySelectorAll('form[data-save-workspace]').forEach(form => {
  form.addEventListener('submit', () => {
    form.elements.namedItem('workspace_json').value = JSON.stringify(
      Blockly.serialization.workspaces.save(workspace)
    );
  });
});

const task = document.getElementById('screen-task');
const status = document.getElementById('screen-status');

// Convert a connected punch/if stack into indented text such as
// "if zombie\n  punch zombie". The checker reads this text, not Blockly objects.
function punchBlocksToText(block, indent = '') {
  let text = '';
  for (; block; block = block.getNextBlock()) {
    if (block.type === 'screen_punch') {
      text += `${indent}punch zombie\n`;
    } else if (block.type === 'controls_if') {
      const condition = block.getInputTargetBlock('IF0');
      text += `${indent}if ${condition ? 'zombie' : '(empty)'}\n`;
      text += punchBlocksToText(block.getInputTargetBlock('DO0'), indent + '  ');
    }
  }
  return text;
}

// Convert live blocks and room IDs into a /check/ request containing assignments or punch text.
function workspaceToBlockCheckRequest(blockWorkspace, roomIds) {
  if (roomIds.lessonId) {
    return {
      mission_id: Number(roomIds.missionId),
      room_id: Number(roomIds.roomId),
      assignments: convertWorkspaceBlocksToAssignments(blockWorkspace)
    };
  }
  return {program: blockWorkspace.getTopBlocks(true).map(block => punchBlocksToText(block)).join('')};
}

// POST assignments or punch text as JSON to /check/ and return {variables, actions} or {punched, reason}.
async function fetchAssignmentStateOrPunchResult(blockCheckRequest) {
  const response = await fetch(task.dataset.checkUrl, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': task.dataset.csrfToken},
    body: JSON.stringify(blockCheckRequest)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'The program could not be run.');
  return data;
}

// Write returned variable values, or the punch outcome and explanation, into
// #screen-status. This displays text; it does not animate or save zombie state.
function showVariableValuesOrPunchMessage(result) {
  if (result.variables) {
    status.textContent = Object.entries(result.variables)
      .map(([name, value]) => `${name} = ${value}`).join(', ');
    return;
  }
  status.textContent = `${result.punched ? '✓ The zombie was punched!' : '✗ The zombie was not punched.'} ${result.reason}`;
}

runButton.addEventListener('click', async () => {
  runButton.disabled = true;
  status.textContent = 'Running your program...';
  try {
    const blockCheckRequest = workspaceToBlockCheckRequest(workspace, task.dataset);
    const checkResponse = await fetchAssignmentStateOrPunchResult(blockCheckRequest);
    showVariableValuesOrPunchMessage(checkResponse);
  } catch (error) {
    console.error('[screen] Run failed', error);
    status.textContent = error.message || 'Something went wrong running your program.';
  } finally {
    runButton.disabled = false;
  }
});

resetButton.addEventListener('click', () => { status.textContent = ''; });


window.addEventListener('resize', () => Blockly.svgResize(workspace));
