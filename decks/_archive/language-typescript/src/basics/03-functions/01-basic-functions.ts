/**
 * 01-basic-functions.ts
 */
export {};

function add(a: number, b: number): number {
	return a + b;
}

const subtract = (a: number, b: number): number => a - b;

console.log(add(1, 2), subtract(10, 5));
