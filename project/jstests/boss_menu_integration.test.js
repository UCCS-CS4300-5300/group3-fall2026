// @vitest-environment jsdom
import {afterEach, beforeEach, expect, test, vi} from 'vitest';
import {Blockly} from '../core/static/core/blockly/blockly_setup.js';
import {BossFlyout} from '../core/static/core/blockly/boss_flyout.js';
import {createWorkspaceController} from '../core/static/core/blockly/workspace_controller.js';

let controller;
let workspace;
const originalBlockDefinitions = {...Blockly.Blocks};

beforeEach(() => {
  // jsdom has no SVG layout engine or canvas text measurement. Supply only
  // those browser measurements; Blockly injection, categories, rendering,
  // capacity checks, and pointer listeners below are the real production code.
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({
    measureText: text => ({width: String(text).length * 8})
  });
  vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
  Object.defineProperty(SVGElement.prototype, 'getBBox', {
    configurable: true,
    value() { return {x: 0, y: 0, width: this.textContent.length * 8, height: 16}; }
  });
  document.body.innerHTML = `
    <div class="boss-screen"><div id="blockly-workspace" style="width:1000px;height:700px"></div></div>
    <p id="block-allowances"></p>
    <script id="screen-workspace-state" type="application/json">{}</script>`;
  controller = createWorkspaceController(document, {
    requested_blocks: ['controls_if', 'boss_undetected', 'boss_make_noise', 'boss_step_back', 'boss_lunge'],
    limits: {controls_if: 3, boss_step_back: 1},
    case_labels: ['lunge'], allow_if_mutation: false
  }, {}, {});
  workspace = Blockly.getMainWorkspace();
});

afterEach(() => {
  if (controller) controller.destroy();
  else Blockly.getMainWorkspace()?.dispose();
  controller = null;
  // Each test injects the application once, just as a real page does. Restore
  // the registry so the next page can register its policy-specific blocks.
  for (const type of Object.keys(Blockly.Blocks)) delete Blockly.Blocks[type];
  Object.assign(Blockly.Blocks, originalBlockDefinitions);
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  delete SVGElement.prototype.getBBox;
  document.body.replaceChildren();
});

function openCategory(name) {
  const toolbox = workspace.getToolbox();
  const category = toolbox.getToolboxItems().find(item => item.getName() === name);
  toolbox.setSelectedItem(category);
  return workspace.getFlyout().getWorkspace().getTopBlocks(false);
}

test('the production boss controller installs the stock menu and every category opens repeatedly', () => {
  expect(workspace.getFlyout().constructor === BossFlyout).toBe(true);
  for (let pass = 0; pass < 3; pass++) {
    for (const name of ['Logic', 'Conditions', 'Actions', 'Zombie actions']) {
      const blocks = openCategory(name);
      expect(blocks.length).toBeGreaterThan(0);
      for (const block of blocks) {
        const root = block.getSvgRoot();
        expect(root.querySelectorAll(':scope > .boss-flyout-stock')).toHaveLength(1);
        expect(root.querySelector('.boss-flyout-stock-label')).not.toBeNull();
      }
      // Stock copies live in SVG. Check their ID namespace without imposing
      // a new constraint on Blockly's native HTML category containers.
      const ids = [...document.querySelectorAll('.boss-screen svg [id]')].map(element => element.id);
      expect(new Set(ids).size).toBe(ids.length);
    }
  }
});

test('category entries retain room for the copies and unlimited stock survives reopening', () => {
  for (let pass = 0; pass < 3; pass++) {
    openCategory('Logic');
    const actions = openCategory('Actions');
    const noise = actions.find(block => block.type === 'boss_make_noise');
    expect(noise.getSvgRoot().querySelectorAll('.boss-flyout-copy')).toHaveLength(2);
    expect(noise.getSvgRoot().querySelector('.boss-flyout-stock-label').textContent).toBe('∞');
    for (let index = 1; index < actions.length; index++) {
      const previous = actions[index - 1].getBoundingRectangleWithoutChildren();
      const next = actions[index].getBoundingRectangleWithoutChildren();
      expect(next.top - previous.bottom).toBeGreaterThanOrEqual(16);
    }
  }
  // Copies are SVG, so merely browsing menus never places a workspace block.
  expect(workspace.getAllBlocks(false)).toHaveLength(0);
});

test('a saved workspace reduces stock immediately when its category is opened', () => {
  Blockly.serialization.workspaces.load({blocks: {languageVersion: 0, blocks: [
    {type: 'controls_if', id: 'saved-if'}
  ]}}, workspace);
  const source = openCategory('Logic')[0];
  expect(source.getSvgRoot().querySelector('.boss-flyout-stock-label').textContent).toBe('2 left');
  expect(source.getSvgRoot().querySelectorAll('.boss-flyout-copy')).toHaveLength(1);
});

test('rapid clicks respect live capacity before queued create events disable the menu block', () => {
  const source = openCategory('Actions').find(block => block.type === 'boss_step_back');
  expect(source.isEnabled()).toBe(true);
  Blockly.serialization.blocks.append({type: 'boss_step_back'}, workspace);
  // Do not wait for the UI's capacity listener. This is the double-click race.
  const root = source.getSvgRoot();
  for (const type of ['pointerdown', 'pointerup', 'dblclick']) {
    const event = new MouseEvent(type, {bubbles: true, cancelable: true, button: 0});
    root.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  }
  for (const key of ['Enter', ' ']) {
    const event = new KeyboardEvent('keydown', {key, bubbles: true, cancelable: true});
    root.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  }
  expect(workspace.getBlocksByType('boss_step_back', false)).toHaveLength(1);
});

test('real block creation, deletion, undo and redo update visible stock', async () => {
  let source = openCategory('Logic')[0];
  const label = () => source.getSvgRoot().querySelector('.boss-flyout-stock-label')?.textContent;
  expect(label()).toBe('3 left');
  Blockly.serialization.blocks.append({type: 'controls_if', id: 'placed-if'}, workspace, {recordUndo: true});
  await vi.waitFor(() => expect(label()).toBe('2 left'));
  workspace.undo(false);
  await vi.waitFor(() => expect(label()).toBe('3 left'));
  workspace.undo(true);
  await vi.waitFor(() => expect(label()).toBe('2 left'));
  workspace.getBlockById('placed-if').dispose(false);
  await vi.waitFor(() => expect(label()).toBe('3 left'));
});

test('exhausted menu blocks cannot be inserted by pointer clicks or double clicks', async () => {
  const source = openCategory('Actions').find(block => block.type === 'boss_step_back');
  const placed = Blockly.serialization.blocks.append({type: 'boss_step_back'}, workspace);
  await vi.waitFor(() => expect(source.isEnabled()).toBe(false));
  const root = source.getSvgRoot();

  for (const type of ['pointerdown', 'pointerup', 'dblclick']) {
    const event = new MouseEvent(type, {bubbles: true, cancelable: true, button: 0});
    root.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  }
  expect(workspace.getBlocksByType('boss_step_back', false)).toHaveLength(1);

  placed.dispose(false);
  await vi.waitFor(() => expect(source.isEnabled()).toBe(true));
  expect(root.querySelector('.boss-flyout-stock-label').textContent).toBe('1 left');
});
