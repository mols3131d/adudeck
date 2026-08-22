/**
 * 03-rest-parameters.ts
 */
export {};

function sumAll(...numbers: number[]): number {
	return numbers.reduce((acc, curr) => acc + curr, 0);
}

console.log(sumAll(1, 2, 3, 4, 5));
