---
title: "Solidity Deep Dive (1): Memory vs. Storage Variable Rules"
date: 2022-04-15 10:00:00 +0900
categories: [Development, Blockchain]
tags: [solidity, ethereum, evm, smart-contract, memory, storage]
image:
  path: /assets/img/posts/solidity/sol1_1.png
description: "Complete rules for how Solidity variables are stored in the EVM — when memory vs. storage is used, reference vs. value copies, and common pitfalls."
---

## Memory vs. Storage in the EVM

Every variable in a Solidity contract is stored in one of two locations within the EVM:

| Location | Scope | Persistence |
|----------|-------|-------------|
| **Storage** | Accessible by all functions in the contract | Permanently stored on-chain across all nodes |
| **Memory** | Local to a function call | Volatile — disappears when the function returns |

## Rules for Variable Storage Location

### Rule 1: State variables are **always** stored in storage

```solidity
uint256 public count; // storage
```

### Rule 2: Function parameters are **always** stored in memory

### Rule 3: Local variables default to memory, with exceptions

| Variable Type | Default Location | Notes |
|--------------|-----------------|-------|
| **Value types** (uint, bool, etc.) | memory | Cannot be declared as `storage` |
| **Reference types** (arrays, structs, strings) | **storage** | Can be overridden to `memory` |
| **Mappings** | **storage only** | Cannot be declared as `memory` at all |

#### 3.1 — Reference types default to storage

#### 3.2 — You can override reference types to memory

#### 3.3 — A local reference-type `storage` variable must point to a state variable

#### 3.4 — Value types cannot be declared as storage inside a function

```solidity
function test() public returns (uint) {
    uint storage myInt; // ❌ Compile error
}
```

#### 3.5 — Mappings are always storage

```solidity
mapping(uint => uint) public intMap;

function test() public returns (uint) {
    mapping(uint => uint) memory map = intMap; // ❌ Error
}

function test2() public returns (uint) {
    mapping(uint => uint) storage map = intMap; // ✅ OK
    map[0] = 11;
    return map[0];
}
```

## Copy Semantics

### Rule 4: Assigning one state variable to another → **value copy**

```solidity
uint stateVal1 = 10;
uint stateVal2 = 20;

function test() public returns (uint) {
    stateVal1 = stateVal2; // both are 20
    stateVal2 = 30;        // stateVal1 is still 20
    return stateVal1;      // returns 20
}
```

### Rule 5: Assigning a memory variable to a storage variable → **value copy**

```solidity
uint[2] stateArr;

function test() public returns (uint) {
    uint[2] memory localArr = [uint(1), 2];
    stateArr = localArr; // both are [1, 2]

    localArr[1] = 10;
    return stateArr[1];  // returns 2, not 10
}
```

### Rule 6: Assigning a state variable to a local memory variable → **value copy**

### Rule 7: Assigning one memory variable to another → **value copy**

---

## 2026 Update Note

- This post was migrated from the original blog and language-polished in 2026.
- Since Solidity 0.8+, the compiler enforces explicit `memory` / `storage` / `calldata` annotations on reference-type parameters, making these rules even more visible at compile time.
