/**
 * 04-enums.ts
 */
export {};

enum Direction {
	Up,
	Down,
	Left,
	Right,
}

const move: Direction = Direction.Up;

console.log({ move, Up: Direction.Up });
