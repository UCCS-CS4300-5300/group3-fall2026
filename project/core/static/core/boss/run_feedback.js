// ===========================================================================
// Display the shared response fields without knowing which boss produced them
// ===========================================================================
export function showRunFeedback(element, result) {
  const lines = [];
  if (result.feedback) lines.push(result.feedback);
  if (result.details) {
    for (const detail of result.details) {
      if (detail) lines.push(detail);
    }
  }
  element.textContent = lines.join(' ');
}
