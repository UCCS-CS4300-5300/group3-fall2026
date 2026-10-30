import {expect, test} from 'vitest';
import fixture from './png_move_projection_fixture.json';
import {projectPoint, coverTransform, imageToDisplay} from '../png_move.js';

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
