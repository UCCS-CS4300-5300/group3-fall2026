import {Blockly} from '../blockly/blockly_setup.js';
import {registerScreenBlocks} from './screen_blocks.js';
import {convertWorkspaceBlocksToAssignments} from './blockly_assignments.js';
import {initializeMovement} from '@png-movement/png_move.js';

const movement = initializeMovement();

const workspaceElement = document.getElementById('blockly-workspace');
const runButton = document.getElementById('lesson-run');

console.info('[screen] Blockly module evaluated', {
  workspaceFound: Boolean(workspaceElement)
});


const lessonBlockTypes = JSON.parse(
  document.getElementById('screen-available-blocks').textContent
);
const lessonInitialVariables = JSON.parse(
  document.getElementById('screen-initial-variables').textContent
);
registerScreenBlocks(Blockly, {
  integerDefaultValue: lessonInitialVariables.zombie_speed ?? 0,
  integerBounds: Object.hasOwn(lessonInitialVariables, 'zombie_speed')
    ? JSON.parse(document.getElementById('screen-movement-config').textContent) : null
});
const lessonBlockCategories = [
  {name: 'Logic', colour: '210', blockTypes: ['logic_true', 'logic_false', 'controls_if']},
  {name: 'Math', colour: '230', blockTypes: ['math_integer']},
  {name: 'Variables', colour: '290', blockTypes: ['screen_zombie_alive', 'screen_zombie_speed']},
  {name: 'Game', colour: '290', blockTypes: ['screen_punch', 'screen_zombie']},
  {name: 'Register', colour: '20', blockTypes: ['screen_cashier_cans', 'screen_cashier_price', 'screen_cashier_total', 'screen_cashier_print']}
];

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
    kind: 'categoryToolbox',
    contents: lessonBlockCategories.map(({blockTypes, ...category}) => ({
      kind: 'category',
      ...category,
      contents: blockTypes.filter(type => lessonBlockTypes.includes(type))
        .map(type => ({kind: 'block', type}))
    })).filter(category => category.contents.length > 0)
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

// Convert connected punch/if blocks into indented text for the program checker.
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
async function fetchAssignmentStateOrPunchResult(blockCheckRequest, signal) {
  const response = await fetch(task.dataset.checkUrl, {
    method: 'POST',
    signal,
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': task.dataset.csrfToken},
    body: JSON.stringify(blockCheckRequest)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'The program could not be run.');
  return data;
}

// Show lesson feedback and final variable values, or the punch outcome, in #screen-status.
function showVariableValuesOrPunchMessage(result) {
  if (result.variables) {
    const variableValues = Object.entries(result.variables)
      .map(([name, value]) => `${name} = ${value}`).join(', ');
    status.textContent = `${result.feedback} ${variableValues}`;
    return;
  }
  status.textContent = `${result.punched ? '✓ The zombie was punched!' : '✗ The zombie was not punched.'} ${result.reason}`;
}

let runGeneration = 0;
let runPending = false;
let pendingRequest = null;

function updateRunAvailability() {
  runButton.disabled = runPending || !movement.isReady();
}

movement.onReady(updateRunAvailability);

function cancelActiveRun() {
  runGeneration += 1;
  pendingRequest?.abort();
  pendingRequest = null;
  runPending = false;
  movement.reset();
  updateRunAvailability();
}

runButton.addEventListener('click', async () => {
  const generation = ++runGeneration;
  pendingRequest?.abort();
  pendingRequest = new AbortController();
  runPending = true;
  runButton.disabled = true;
  status.textContent = 'Running your program...';
  const attempt = movement.start(lessonInitialVariables.zombie_speed);
  try {
    const blockCheckRequest = workspaceToBlockCheckRequest(workspace, task.dataset);
    const checkResponse = await fetchAssignmentStateOrPunchResult(blockCheckRequest, pendingRequest.signal);
    if (generation !== runGeneration) return;

    movement.applyResult(attempt, checkResponse);
    showVariableValuesOrPunchMessage(checkResponse);
  } catch (error) {
    if (generation !== runGeneration) return;

    movement.fail(attempt);
    console.error('[screen] Run failed', error);
    status.textContent = error.message || 'Something went wrong running your program.';
  } finally {
    if (generation === runGeneration) {
      pendingRequest = null;
      runPending = false;
      updateRunAvailability();
    }
  }
});

document.querySelectorAll('form[data-save-workspace]').forEach(form => {
  form.addEventListener('submit', cancelActiveRun);
});
window.addEventListener('pagehide', cancelActiveRun);


window.addEventListener('resize', () => Blockly.svgResize(workspace));
