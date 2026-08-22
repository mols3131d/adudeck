# 01. Basic Types (기본 타입)

TypeScript는 JavaScript의 동적 타입 시스템에 **완전한 정적 타입**을 부여하여 코드의 안정성을 높입니다. 이번 장에서는 기초가 되는 원시 타입부터 특수한 타입들을 학습합니다.

---

## 📘 주제별 실습 안내

각 개념은 독립적인 파일로 분리되어 있습니다. 순서대로 실습하며 감을 익혀보세요.

### 1. 원시 타입 (Primitive Types)
- **파일**: `01-primitive-types.ts`
- **설명**: `string`, `number`, `boolean` 등 가장 기초적인 데이터를 다룹니다.
```typescript
const age: number = 25;
const name: string = "Alice";
```

### 2. 배열 (Arrays)
- **파일**: `02-arrays.ts`
- **설명**: 동일한 타입의 데이터 집합을 정의합니다. `type[]` 또는 `Array<type>` 형식을 사용합니다.
```typescript
const list: number[] = [1, 2, 3];
```

### 3. 튜플 (Tuples)
- **파일**: `03-tuples.ts`
- **설명**: 요소의 개수와 각 요소의 타입이 고정된 배열입니다. 각 위치마다 다른 타입을 지정할 수 있습니다.
```typescript
let x: [string, number] = ["hello", 10];
```

### 4. 열거형 (Enums)
- **파일**: `04-enums.ts`
- **설명**: 명명된 숫자 또는 문자열 상수의 집합을 정의할 때 사용합니다. 코드의 가독성과 의도를 명확히 합니다.
```typescript
enum Color { Red, Green, Blue }
let c: Color = Color.Green;
```

---

## 💡 학습 포인트

1. **타입 추론(Inference)**: 모든 곳에 타입을 명시할 필요는 없습니다. TypeScript는 초기값을 보고 타입을 자동으로 추측하기도 합니다.
2. **엄격성**: 선언된 타입과 다른 형식의 값을 할당하려고 하면 컴파일 단계에서 즉시 에러를 발생시켜 버그를 방지합니다.

---

> [!IMPORTANT]
> 실습 파일 상단의 `export {};` 구문은 해당 파일을 독립적인 모듈로 취급하게 하여, 다른 파일과의 변수 이름 충돌을 방지하기 위함입니다.
