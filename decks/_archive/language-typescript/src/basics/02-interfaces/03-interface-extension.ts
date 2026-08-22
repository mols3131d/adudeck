/**
 * 03-interface-extension.ts
 */
export {};

interface Shape {
	color: string;
}

interface Square extends Shape {
	sideLength: number;
}

const square: Square = {
	color: "blue",
	sideLength: 10,
};

console.log(square);
