/*
 * Map engine adapted from Blockly Games Map's core movement/log model.
 * Original project: https://github.com/blockly-games/blockly-games
 * Original license: Apache-2.0
 */

export const Direction = Object.freeze({NORTH: 0, EAST: 1, SOUTH: 2, WEST: 3});
export const Square = Object.freeze({WALL: 0, OPEN: 1, START: 2, FINISH: 3});

export class MapEngine {
  constructor(map) {
    this.map = map;
    this.rows = map.length;
    this.cols = map[0].length;
    this.log = [];
    this.reset();
  }

  reset() {
    this.log.length = 0;
    this.position = this.findSquare(Square.START);
    this.finish = this.findSquare(Square.FINISH);
    this.direction = Direction.EAST;
  }

  findSquare(type) {
    for (let y = 0; y < this.rows; y++) {
      for (let x = 0; x < this.cols; x++) {
        if (this.map[y][x] === type) return {x, y};
      }
    }
    throw new Error(`Map has no square of type ${type}`);
  }

  normalizeDirection(direction) {
    return ((direction % 4) + 4) % 4;
  }

  target(directionOffset) {
    const d = this.normalizeDirection(this.direction + directionOffset);
    const {x, y} = this.position;
    if (d === Direction.NORTH) return {x, y: y - 1};
    if (d === Direction.EAST) return {x: x + 1, y};
    if (d === Direction.SOUTH) return {x, y: y + 1};
    return {x: x - 1, y};
  }

  isPath(directionOffset, blockId = null) {
    const p = this.target(directionOffset);
    const square = this.map[p.y]?.[p.x];
    const d = this.normalizeDirection(this.direction + directionOffset);
    if (blockId) this.log.push({type: 'look', direction: d, blockId});
    return square !== undefined && square !== Square.WALL;
  }

  move(directionOffset, blockId) {
    if (!this.isPath(directionOffset)) {
      this.log.push({type: 'fail', direction: directionOffset ? 'backward' : 'forward', blockId});
      throw new Error('Map collision');
    }

    const p = this.target(directionOffset);
    const d = this.normalizeDirection(this.direction + directionOffset);
    this.position = p;
    this.log.push({type: 'move', direction: d, blockId});

    if (this.position.x === this.finish.x && this.position.y === this.finish.y) {
      throw {mapSuccess: true};
    }
  }

  turn(offset, blockId) {
    this.direction = this.normalizeDirection(this.direction + (offset ? 1 : -1));
    this.log.push({type: offset ? 'right' : 'left', blockId});
  }

  notDone() {
    return this.position.x !== this.finish.x || this.position.y !== this.finish.y;
  }
}
