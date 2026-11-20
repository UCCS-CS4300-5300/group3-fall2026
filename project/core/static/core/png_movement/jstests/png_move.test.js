import {expect, test} from 'vitest';
import fixture from './png_move_projection_fixture.json';
import {projectPoint, coverTransform, imageToDisplay, getTranslationPose} from '../png_move.js';

test('custom starting height transitions smoothly to the final perspective height', () => {
  const floor = {
    matrix: [1, 0, 0, 0, 1, 0, 0, -0.5, 1],
    motion: {start_floor: [0, 0], end_floor: [0, 1], duration_ms: 1000,
      start_height: 0.4, end_height: 0.6, end_depth: 0.5}
  };
  expect(getTranslationPose(floor, 0).height).toBeCloseTo(0.4);
  expect(getTranslationPose(floor, 500).height).toBeCloseTo(0.35 / 0.75);
  expect(getTranslationPose(floor, 1000).height).toBeCloseTo(0.6);
});

// One cross-language reference guards the Python/JavaScript matrix convention.
test('projects the reference interior point', () => {
  const sample = fixture.samples.at(-1);
  expect(projectPoint(fixture.matrix, sample.floor)).toEqual(
    sample.image.map(value => expect.closeTo(value, 10))
  );
});

test.each([
  {name: 'wide', dimensions: [1000, 500, 500, 500], corners: [[-250, 0], [750, 500]]},
  {name: 'tall', dimensions: [500, 1000, 500, 500], corners: [[0, -250], [500, 750]]}
])('aligns the overlay with a $name background', ({dimensions, corners}) => {
  const transform = coverTransform(...dimensions);
  expect([[0, 0], [1, 1]].map(point => imageToDisplay(point, transform))).toEqual(corners);
});
