import {Blockly} from './blockly_setup.js';

const SVG_NS = 'http://www.w3.org/2000/svg';
const GUARDED_EVENTS = ['pointerdown', 'pointerup', 'dblclick', 'keydown'];

/**
 * Input: one rendered flyout block and its remaining per-type capacity.
 * Output: decorative SVG only; Blockly still owns exactly one draggable block.
 * Infinity uses three layers. Finite stock uses one layer per remaining block.
 */
export function drawFlyoutStock(block, remaining) {
  const root = block.getSvgRoot();
  root.querySelector(':scope > .boss-flyout-stock')?.remove();

  const decoration = document.createElementNS(SVG_NS, 'g');
  decoration.setAttribute('class', 'boss-flyout-stock');
  decoration.setAttribute('aria-hidden', 'true');

  const unlimited = remaining === Infinity;
  const layers = unlimited ? 3 : Math.max(1, remaining);
  // Keep the deepest copy within the native flyout's existing 24-unit gap.
  // Counts can shrink without moving the actual block or its hit target.
  const offset = Math.min(4, 16 / Math.max(1, layers - 1));

  for (let depth = layers - 1; depth >= 1; depth--) {
    const copy = root.cloneNode(true);
    for (const element of [copy, ...copy.querySelectorAll('*')]) {
      for (const attribute of [...element.attributes]) {
        if (['id', 'data-id', 'tabindex', 'role'].includes(attribute.name)
            || attribute.name.startsWith('aria-')) {
          element.removeAttribute(attribute.name);
        }
      }
    }
    copy.setAttribute('class', 'boss-flyout-copy');
    copy.setAttribute('transform', `translate(${depth * offset}, ${depth * offset})`);
    copy.setAttribute('opacity', String(unlimited ? 0.75 - depth * 0.1 : Math.max(0.2, 0.55 - depth * 0.06)));
    decoration.append(copy);
  }

  const label = document.createElementNS(SVG_NS, 'text');
  label.setAttribute('class', 'boss-flyout-stock-label');
  label.setAttribute('x', String(block.width - 2));
  label.setAttribute('y', String(block.height + 13));
  label.setAttribute('text-anchor', 'end');
  label.textContent = unlimited ? '∞' : `${remaining} left`;
  decoration.append(label);

  root.insertBefore(decoration, root.firstChild);
  block.getFocusableElement().setAttribute('aria-description',
    unlimited ? 'Unlimited blocks available' : `${remaining} blocks remaining`);
}

/**
 * Boss-only flyout plugin. Native Blockly still lays out, drags, serializes,
 * and disables blocks; this subclass decorates them and guards click insertion.
 */
export class BossFlyout extends Blockly.VerticalFlyout {
  constructor(options) {
    super(options);
    this.onInventoryChange = event => {
      if (event.type === Blockly.Events.BLOCK_CREATE || event.type === Blockly.Events.BLOCK_DELETE) {
        this.updateStock();
      }
    };
    this.guardInsertion = event => {
      if (event.type === 'keydown' && !['Enter', ' '].includes(event.key)) return;

      const block = this.getWorkspace().getTopBlocks(false)
        .find(candidate => candidate.getSvgRoot().contains(event.target));
      if (!block) return;

      // Blockly's autoclosing flyout click handler can append a disabled block.
      // Recheck live capacity before that handler runs. This also closes the
      // rapid-click gap before Blockly's queued create event updates the flyout.
      const target = this.getTargetWorkspace();
      if (!block.isEnabled() || !target.isCapacityAvailable(Blockly.common.getBlockTypeCounts(block))) {
        event.preventDefault();
        event.stopImmediatePropagation();
      }
    };
  }

  createDom(tagName) {
    const root = super.createDom(tagName);
    this.stockRoot = root;
    for (const type of GUARDED_EVENTS) root.addEventListener(type, this.guardInsertion, true);
    return root;
  }

  init(targetWorkspace) {
    super.init(targetWorkspace);
    targetWorkspace.addChangeListener(this.onInventoryChange);
  }

  reflow() {
    super.reflow();
    this.updateStock();
  }

  updateStock() {
    const target = this.getTargetWorkspace();
    if (!target) return;
    for (const block of this.getWorkspace().getTopBlocks(false)) {
      drawFlyoutStock(block, Math.max(0, target.remainingCapacityOfType(block.type)));
    }
  }

  dispose() {
    this.getTargetWorkspace()?.removeChangeListener(this.onInventoryChange);
    for (const type of GUARDED_EVENTS) this.stockRoot?.removeEventListener(type, this.guardInsertion, true);
    super.dispose();
  }
}
