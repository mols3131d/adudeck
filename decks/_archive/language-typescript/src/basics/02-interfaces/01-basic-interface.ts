/**
 * 01-basic-interface.ts
 */
export {};

interface User {
	id: number;
	name: string;
}

const user: User = {
	id: 1,
	name: "Alice",
};

console.log(user);
