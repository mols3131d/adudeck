# 00. Output (출력)

프로그래밍의 첫걸음은 코드가 실행된 결과를 눈으로 확인하는 것입니다. TypeScript(및 JavaScript)에서 가장 널리 사용되는
출력 도구인 `console.log()`의 다양한 활용법을 알아봅니다.

---

## 📘 핵심 개념 및 실습 해설

`01-console-log.ts` 실습 파일의 내용을 바탕으로 주요 문법을 설명합니다.

### 1. 기본적인 값 출력

가장 단순한 형태의 출력입니다. 문자열, 숫자, 불리언 등 어떤 타입의 값도 출력할 수 있습니다.

```typescript
// 문자열 출력
console.log("Hello TypeScript!");

// 숫자 출력
console.log(2026);
```

### 2. 여러 값의 동시 출력

쉼표(`,`)를 사용하여 여러 데이터를 한 줄에 출력할 수 있습니다. 각 값 사이에는 자동으로 공백이 한 칸 추가됩니다.

```typescript
const name = "Antigravity";
const version = "1.0.0";

// 텍스트 설명과 변수 값을 함께 출력할 때 유용합니다.
console.log("Agent:", name, "Version:", version);
```

### 3. 객체 디버깅 (Object Logging)

변수가 많아질수록 어떤 값이 어떤 변수의 것인지 헷갈릴 수 있습니다. 이때 중괄호(`{}`)를 사용하여 **객체 형태**로 감싸주면
변수 이름과 값을 쌍으로 확인할 수 있어 매우 효율적입니다.

```typescript
const profile = {
  language: "TypeScript",
  difficulty: "Easy",
};

// 프로퍼티 이름과 값을 함께 출력
console.log({ profile });

// 여러 변수를 한꺼번에 객체로 묶어서 출력 (속성 단축 구문)
console.log({ name, version }); // 출력 결과: { name: "Antigravity", version: "1.0.0" }
```

### 4. 표현식 결과 출력

`console.log()` 내부에서 연산을 수행하고 그 결과를 즉시 출력할 수 있습니다.

```typescript
console.log("1 + 1 =", 1 + 1); // 1 + 1 = 2
```

---

## 🛠️ 실행 및 확인 방법

작성한 코드를 터미널에서 실행하여 결과를 확인하는 방법은 다음과 같습니다.

1. **ts-node 사용 (권장)**: 컴파일 과정 없이 즉시 실행

   ```bash
   npx ts-node src/basics/00-output/01-console-log.ts
   ```

2. **Vitest 사용**: 테스트 환경에서 출력 확인

   ```bash
   npm test src/basics/00-output/01-console-log.ts
   ```

---

> [!TIP]
> 실무에서는 단순히 `console.log` 외에도 `console.error` (에러 출력), `console.warn` (경고 출력), `console.table` (표
> 형식 출력) 등 다양한 메서드를 상황에 맞춰 활용합니다.
