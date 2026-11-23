// @vitest-environment jsdom
import {expect, test} from 'vitest';
import {drawFlyoutStock} from '../core/static/core/blockly/boss_flyout.js';

function stockBlock() {
  const root = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  root.setAttribute('id', 'real-block');
  root.innerHTML = '<path id="real-path" data-id="source" tabindex="0" d="M0 0H100V30H0Z"/><text>wait</text>';
  return {width: 100, height: 30, getSvgRoot: () => root, getFocusableElement: () => root};
}

test('remaining stock draws copies behind one real block without duplicate IDs or focus targets', () => {
  const block = stockBlock();
  drawFlyoutStock(block, 3);
  const root = block.getSvgRoot();
  const decoration = root.firstElementChild;
  expect(decoration.classList.contains('boss-flyout-stock')).toBe(true);
  expect(decoration.getAttribute('aria-hidden')).toBe('true');
  expect(decoration.querySelectorAll('.boss-flyout-copy')).toHaveLength(2);
  expect(decoration.querySelectorAll('[id], [data-id], [tabindex]')).toHaveLength(0);
  expect(root.querySelectorAll('#real-path')).toHaveLength(1);

  drawFlyoutStock(block, 2);
  expect(root.querySelectorAll('.boss-flyout-copy')).toHaveLength(1);
  drawFlyoutStock(block, 0);
  expect(root.querySelectorAll('.boss-flyout-copy')).toHaveLength(0);
  expect(root.querySelector('.boss-flyout-stock-label').textContent).toBe('0 left');
  expect(root.getAttribute('aria-description')).toBe('0 blocks remaining');
});

test('unlimited blocks have three layers with less fading than finite stock', () => {
  const block = stockBlock();
  drawFlyoutStock(block, 3);
  const finiteOpacity = Number(block.getSvgRoot().querySelector('.boss-flyout-copy').getAttribute('opacity'));
  drawFlyoutStock(block, Infinity);
  const copies = block.getSvgRoot().querySelectorAll('.boss-flyout-copy');
  expect(copies).toHaveLength(2);
  expect(Number(copies[0].getAttribute('opacity'))).toBeGreaterThan(finiteOpacity);
  expect(block.getSvgRoot().querySelector('.boss-flyout-stock-label').textContent).toBe('∞');
});

