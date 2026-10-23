const toggle = document.getElementById('tutorial-toggle');
const close = document.getElementById('tutorial-close');
const panel = document.getElementById('tutorial-panel');
const columns = document.querySelector('.columns');
const selector = document.getElementById('tutorial-select');
const content = document.getElementById('tutorial-content');

function appendInlineMarkdown(parent, text) {
  const tokenPattern = /(`+)(.+?)\1|\[([^\]]+)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)|\*\*(.+?)\*\*|__(.+?)__|\*([^*\n]+)\*|_([^_\n]+)_|~~(.+?)~~/g;
  let previousEnd = 0;

  for (const match of text.matchAll(tokenPattern)) {
    parent.append(document.createTextNode(text.slice(previousEnd, match.index)));
    let node;
    if (match[1]) {
      node = document.createElement('code');
      node.textContent = match[2];
    } else if (match[3]) {
      let url;
      try {
        url = new URL(match[4], window.location.href);
      } catch {
        url = null;
      }
      if (!url || !['http:', 'https:', 'mailto:'].includes(url.protocol)) {
        node = document.createTextNode(match[0]);
      } else {
        node = document.createElement('a');
        node.href = url.href;
        node.title = match[5] || '';
        appendInlineMarkdown(node, match[3]);
      }
    } else {
      const contentText = match[6] || match[7] || match[8] || match[9] || match[10];
      const tagName = match[6] || match[7] ? 'strong'
        : match[8] || match[9] ? 'em' : 'del';
      node = document.createElement(tagName);
      appendInlineMarkdown(node, contentText);
    }
    parent.append(node);
    previousEnd = match.index + match[0].length;
  }

  parent.append(document.createTextNode(text.slice(previousEnd)));
}

function renderMarkdown(markdown) {
  const fragment = document.createDocumentFragment();
  const lines = markdown.replace(/\r\n?/g, '\n').split('\n');
  const isBlockStart = line => /^\s*(?:#{1,6}\s|```|~~~|>|[-*+]\s|\d+[.)]\s|(?:[-*_]\s*){3,}$)/.test(line);
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }

    const fence = line.match(/^\s*(```+|~~~+)/);
    if (fence) {
      const codeLines = [];
      index += 1;
      while (index < lines.length && !lines[index].trimStart().startsWith(fence[1])) {
        codeLines.push(lines[index]);
        index += 1;
      }
      if (index < lines.length) index += 1;
      const pre = document.createElement('pre');
      const code = document.createElement('code');
      code.textContent = codeLines.join('\n');
      pre.append(code);
      fragment.append(pre);
      continue;
    }

    const heading = line.match(/^\s*(#{1,6})\s+(.+?)\s*#*\s*$/);
    if (heading) {
      const element = document.createElement(`h${heading[1].length}`);
      appendInlineMarkdown(element, heading[2]);
      fragment.append(element);
      index += 1;
      continue;
    }

    if (/^\s*(?:(?:[-*_]\s*){3,})$/.test(line)) {
      fragment.append(document.createElement('hr'));
      index += 1;
      continue;
    }

    if (/^\s*>/.test(line)) {
      const quoteLines = [];
      while (index < lines.length && /^\s*>/.test(lines[index])) {
        quoteLines.push(lines[index].replace(/^\s*>\s?/, ''));
        index += 1;
      }
      const quote = document.createElement('blockquote');
      quote.append(renderMarkdown(quoteLines.join('\n')));
      fragment.append(quote);
      continue;
    }

    const listItem = line.match(/^\s*((?:[-*+])|(?:\d+[.)]))\s+(.+)$/);
    if (listItem) {
      const ordered = /^\d/.test(listItem[1]);
      const list = document.createElement(ordered ? 'ol' : 'ul');
      while (index < lines.length) {
        const item = lines[index].match(/^\s*((?:[-*+])|(?:\d+[.)]))\s+(.+)$/);
        if (!item || /^\d/.test(item[1]) !== ordered) break;
        const element = document.createElement('li');
        appendInlineMarkdown(element, item[2]);
        list.append(element);
        index += 1;
      }
      fragment.append(list);
      continue;
    }

    const paragraphLines = [line.trim()];
    index += 1;
    while (index < lines.length && lines[index].trim() && !isBlockStart(lines[index])) {
      paragraphLines.push(lines[index].trim());
      index += 1;
    }
    const paragraph = document.createElement('p');
    appendInlineMarkdown(paragraph, paragraphLines.join(' '));
    fragment.append(paragraph);
  }

  return fragment;
}

if (toggle && close && panel && columns && selector && content) {
  let activeRequest;

  function setPanelOpen(open) {
    panel.hidden = !open;
    columns.classList.toggle('tutorial-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    if (open && selector.value) loadTutorial(selector.value);
    if (!open && activeRequest) activeRequest.abort();
  }

  async function loadTutorial(url) {
    if (activeRequest) activeRequest.abort();
    activeRequest = new AbortController();
    content.textContent = 'Loading tutorial...';

    try {
      const response = await fetch(url, {signal: activeRequest.signal});
      if (!response.ok) {
        throw new Error(`Tutorial request failed with HTTP ${response.status}.`);
      }
      content.replaceChildren(renderMarkdown(await response.text()));
    } catch (error) {
      if (error.name === 'AbortError') return;
      console.error('[screen] Tutorial document failed to load', error);
      content.textContent = 'Unable to load this tutorial document. Please try again.';
    }
  }

  toggle.addEventListener('click', () => setPanelOpen(panel.hidden));
  close.addEventListener('click', () => setPanelOpen(false));
  selector.addEventListener('change', () => loadTutorial(selector.value));
}
