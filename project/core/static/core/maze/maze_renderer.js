export class MazeRenderer {
  constructor(container) {
    this.container = container;
    this.tileSize = 50;
    this.svg = null;
    this.player = null;
  }

  draw(engine) {
    this.container.replaceChildren();
    const width = engine.cols * this.tileSize;
    const height = engine.rows * this.tileSize;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.classList.add('maze-svg');
    this.svg = svg;

    for (let y = 0; y < engine.rows; y++) {
      for (let x = 0; x < engine.cols; x++) {
        const square = engine.map[y][x];
        const rect = document.createElementNS(svg.namespaceURI, 'rect');
        rect.setAttribute('x', x * this.tileSize);
        rect.setAttribute('y', y * this.tileSize);
        rect.setAttribute('width', this.tileSize);
        rect.setAttribute('height', this.tileSize);
        rect.classList.add(square === 0 ? 'maze-wall' : 'maze-path');
        svg.appendChild(rect);

        if (square === 3) {
          const goal = document.createElementNS(svg.namespaceURI, 'circle');
          goal.setAttribute('cx', x * this.tileSize + 25);
          goal.setAttribute('cy', y * this.tileSize + 25);
          goal.setAttribute('r', 13);
          goal.classList.add('maze-goal');
          svg.appendChild(goal);
        }
      }
    }

    const player = document.createElementNS(svg.namespaceURI, 'polygon');
    player.setAttribute('points', '0,-15 13,12 -13,12');
    player.classList.add('maze-player');
    this.player = player;
    svg.appendChild(player);
    this.container.appendChild(svg);
    this.setPlayer(engine.position, engine.direction);
  }

  setPlayer(position, direction) {
    if (!this.player) return;
    const x = position.x * this.tileSize + 25;
    const y = position.y * this.tileSize + 25;
    this.player.setAttribute('transform', `translate(${x} ${y}) rotate(${direction * 90})`);
  }

  async replay(log, engine, highlight) {
    for (const action of log) {
      if (action.blockId) highlight(action.blockId);
      if (action.type === 'move') {
        await this.wait(120);
        this.setPlayer(engine.position, engine.direction);
      } else if (action.type === 'left' || action.type === 'right') {
        await this.wait(120);
      } else {
        await this.wait(80);
      }
    }
    highlight(null);
  }

  wait(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
}
