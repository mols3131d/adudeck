/**
 * 02-optional-readonly.ts
 */
export {};

interface Post {
	readonly id: number;
	title: string;
	author?: string;
}

const post: Post = {
	id: 100,
	title: "Atomic Learning",
};

// post.id = 101; // Error: readonly

console.log(post);
