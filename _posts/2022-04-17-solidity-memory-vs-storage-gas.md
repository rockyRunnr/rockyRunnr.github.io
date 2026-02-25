---
title: "Solidity Deep Dive (2): Is Memory Always Cheaper Than Storage?"
date: 2022-04-17 10:00:00 +0900
categories: [Development, Blockchain]
tags: [solidity, ethereum, evm, gas-optimization, smart-contract]
image:
  path: /assets/img/posts/solidity/sol2_1.png
description: "Exploring the gas cost trade-off between memory and storage reference variables in Solidity — when storage is actually cheaper."
---

## The Question

While studying the [Magic Dragon DAO](https://app.magicdragon.lol/) contracts, I noticed something odd in the `_removeZeroStakes` function. The `Stake` struct variable `s` is declared with the `storage` keyword inside a for loop, even though it is only read (not written):

```solidity
function _removeZeroStakes() internal {
    bool shouldRecurse = stakes.length > 0;

    for (uint256 i = 0; i < stakes.length; i++) {
        _updateStakeDepositAmount(i);

        Stake storage s = stakes[i]; // Why storage, not memory?

        if (s.amount == 0) {
            _removeStake(i);
            break;
        }

        if (i == stakes.length - 1) {
            shouldRecurse = false;
        }
    }

    if (shouldRecurse) {
        _removeZeroStakes();
    }
}
```

Shouldn't `memory` always be cheaper since the data doesn't need to persist on-chain?

## The Answer: Not Always

When you assign a **storage reference** to a **memory variable**, the EVM must:

1. Allocate new memory space (additional gas cost).
2. Copy the struct contents from storage into memory.

Each subsequent access uses `MLOAD` (cheap), but the **upfront allocation cost** is non-trivial.

When you declare a **storage reference**, there is:

- No memory allocation cost.
- Just a single `SLOAD` per field access.

## Rule of Thumb

| Access Count | Recommended Keyword |
|:------------:|:-------------------:|
| ≤ 4          | `storage`           |
| > 4          | `memory`            |

With four or fewer accesses, the overhead of memory allocation outweighs the per-access savings of `MLOAD` over `SLOAD`. Beyond that threshold, `memory` becomes cheaper overall. [[1]](https://ethereum.stackexchange.com/questions/66382/switching-from-storage-to-memory-increases-the-gas-cost)

In the example above, only **one field** (`s.amount`) is accessed, so `Stake storage s` is indeed the gas-optimal choice.

---

### Reference

[1] [Switching from storage to memory increases the gas cost — Ethereum Stack Exchange](https://ethereum.stackexchange.com/questions/66382/switching-from-storage-to-memory-increases-the-gas-cost)

## 2026 Update Note

- This post was migrated from the original blog and language-polished in 2026.
- Gas costs for `SLOAD` and memory expansion have been adjusted by multiple EIPs since 2022 (e.g., EIP-2929 cold/warm access). The general principle still holds, but exact break-even points may differ on current mainnet.
