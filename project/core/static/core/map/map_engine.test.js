import {describe, test, expect} from 'vitest';
import {MapEngine, Direction} from './map_engine.js';

// Test fixture, not a real level. 0 = wall, 1 = open, 2 = start, 3 = finish.
// Start (1,2) facing east, a junction at (2,2) with a side path north at (2,1), finish (3,2).
const testMap = [
  [0, 0, 0, 0, 0],
  [0, 0, 1, 0, 0],
  [0, 2, 1, 3, 0],
  [0, 0, 0, 0, 0],
];
const makeEngine = () => new MapEngine(testMap);
const start = {x: 1, y: 2};
const junction = {x: 2, y: 2};

describe('map engine (works on any map)', () => {
  test('starts on the start square facing east', () => {
    const engine = makeEngine();

    expect(engine.position).toEqual(start);
    expect(engine.direction).toBe(Direction.EAST);
    expect(engine.notDone()).toBe(true);
  });

  test('moving forward once does not win', () => {
    const engine = makeEngine();

    engine.move(0, 'b1');

    expect(engine.position).toEqual(junction);
    expect(engine.notDone()).toBe(true);
  });

  test('reaching the goal signals success', () => {
    const engine = makeEngine();
    engine.move(0, 'b1');

    expect(() => engine.move(0, 'b2')).toThrow(expect.objectContaining({mapSuccess: true}));
    expect(engine.notDone()).toBe(false);
  });

  test('walking into a wall fails and does not move', () => {
    const engine = makeEngine();
    engine.turn(0, 'b1'); // face north, (1,1) is a wall

    expect(() => engine.move(0, 'b2')).toThrow('Map collision');
    expect(engine.position).toEqual(start);
    expect(engine.log.at(-1).type).toBe('fail');
  });

  test('walking off the edge of the map fails', () => {
    const edgeEngine = new MapEngine([[2, 3]]); // one row, so north is outside the grid
    edgeEngine.turn(0, 'b1'); // face north

    expect(() => edgeEngine.move(0, 'b2')).toThrow('Map collision');
    expect(edgeEngine.position).toEqual({x: 0, y: 0});
  });

  test('turning changes direction without moving', () => {
    const engine = makeEngine();

    engine.turn(1, 'b1'); // right: east -> south

    expect(engine.direction).toBe(Direction.SOUTH);
    expect(engine.position).toEqual(start);
  });

  test('isPath tells open squares from walls (ahead, left, right)', () => {
    const engine = makeEngine();
    engine.move(0, 'b1'); // stand on the junction

    expect(engine.isPath(0)).toBe(true);  // ahead (east) is the finish
    expect(engine.isPath(3)).toBe(true);  // left (north) is the side path
    expect(engine.isPath(1)).toBe(false); // right (south) is a wall
  });

  test('reset returns to start and clears the log', () => {
    const engine = makeEngine();
    engine.move(0, 'b1');
    engine.turn(1, 'b2');

    engine.reset();

    expect(engine.position).toEqual(start);
    expect(engine.direction).toBe(Direction.EAST);
    expect(engine.log).toEqual([]);
  });

  test('a map with no start square is rejected', () => {
    expect(() => new MapEngine([[0, 1, 3]])).toThrow('no square of type 2');
  });

  test('a map with no finish square is rejected', () => {
    expect(() => new MapEngine([[0, 2, 1]])).toThrow('no square of type 3');
  });
});
