/**
 * Apply playback decoration to blocks in the player's rendered workspace.
 *
 * Input: a server execution event with block_id/kind, and 'start' or 'end'
 * from the timeline player. Output: one decorated block, or none after clear().
 * This helper does not run blocks or advance time; the zombie's playback clock
 * supplies action/decision display boundaries inside each movement unit. Missing
 * blocks are ignored during teardown.
 */
export function createExecutionHighlighter(workspace) {
  let active = null;

  function clear() {
    if (!active) return;

    active.root.classList.remove(active.className);
    workspace.highlightBlock(null);
    active = null;
  }

  function showStep(event, boundary) {
    if (boundary === 'end') {
      // An older step must not remove a newer block's decoration.
      if (active?.blockId === event.block_id) clear();
      return;
    }
    if (boundary !== 'start') return;
    // Container traversal remains in the execution record for diagnostics,
    // but only actual expressions and actions receive playback decoration.
    if (event.kind !== 'action' && event.kind !== 'condition') return;

    clear();
    const block = workspace.getBlockById(event.block_id);
    if (!block) return;

    const root = block.getSvgRoot();
    if (!root) return;

    const className = event.kind === 'action'
      ? 'boss-execution-action' : 'boss-execution-decision';

    workspace.highlightBlock(event.block_id);
    root.classList.add(className);
    active = {blockId: event.block_id, root, className};
  }

  return {showStep, clear};
}
