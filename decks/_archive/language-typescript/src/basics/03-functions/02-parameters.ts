/**
 * 02-parameters.ts
 */
export {};

function greet(name: string, greeting = "Hello"): string {
	return `${greeting}, ${name}!`;
}

function buildName(first: string, last?: string): string {
	return last ? `${first} ${last}` : first;
}

console.log(greet("User"), buildName("John", "Doe"));
