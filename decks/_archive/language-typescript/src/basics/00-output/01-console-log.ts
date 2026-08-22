/**
 * 01-console-log.ts
 * 다양한 방식으로 데이터를 출력해 봅니다.
 */
export {};

// 1. 단순 값 출력
console.log("Hello TypeScript!");
console.log(2026);

// 2. 여러 값 동시에 출력
const name = "Antigravity";
const version = "1.0.0";
console.log("Agent:", name, "Version:", version);

// 3. 객체 형태로 출력 (변수명과 값을 동시에 확인하기 좋습니다)
const profile = {
	language: "TypeScript",
	difficulty: "Easy",
};
console.log({ profile });
console.log({ name, version }); // 속성 단축 구문

// 4. 숫자 계산 결과 출력
console.log("1 + 1 =", 1 + 1);
