---
title: "Solidity Deep Dive (4): EIP-4337 Account Abstraction — Audit Report Review"
date: 2022-04-29 10:00:00 +0900
categories: [Development, Blockchain]
tags: [solidity, ethereum, eip-4337, account-abstraction, audit, openzeppelin, security]
image:
  path: /assets/img/posts/solidity/sol4_1.png
description: "Key findings from OpenZeppelin's audit of the EIP-4337 Account Abstraction implementation — deposit manipulation, silent token transfer failures, and the dangers of Solidity's transfer()."
---

## Starting the Audit Series

After reading a couple of Solidity books and working through the [official documentation](https://docs.soliditylang.org/), I studied several real-world contracts — Treasure DAO's Market and Mining contracts, and Magic Dragon DAO's Staking & Reward contracts. At this point, I rarely encountered unfamiliar syntax or behavior.

To broaden my exposure, especially around **security**, I decided to review OpenZeppelin audit reports and document key insights. I focus on findings that are educational — there are plenty of typos and arithmetic mistakes in audits that are not worth covering.

## EIP-4337: Ethereum Account Abstraction

The first report is the **EIP-4337 Account Abstraction Audit**. Account Abstraction introduces programmable accounts with features like staking and flexible validation logic.

---

### Finding 1: Deposit Manipulation

**Issue:** The `addStakeTo` function accepted an `address` parameter and added funds to **the caller's balance** instead of the specified `account` balance. This allowed anyone to manipulate (effectively steal) deposits from any account.

**Fix:** Renamed to `addStake` and restricted so that callers can only add value to **their own** stake ([PR #50](https://github.com/eth-infinitism/account-abstraction/pull/50/files)).

> **Takeaway:** Whenever a mapping is accessed via an `address` parameter, verify that proper access control exists — check `msg.sender` or use an `onlyOwner`-style modifier.

---

### Finding 2: Token Transfers May Fail Silently

**Issue:** The `DepositPaymaster` contract did not check the return value of ERC-20 `transfer` / `transferFrom` calls during deposit, withdrawal, and gas-cost recovery. While many tokens revert on failure, the [ERC-20 standard](https://eips.ethereum.org/EIPS/eip-20) only specifies a **boolean return value**. Tokens like the [0x Protocol Token](https://etherscan.io/address/0xe41d2489571d322189246dafa5ebde1f4699f498) return `false` instead of reverting, causing **silent failures** and incorrect internal accounting.

**Fix:** Switched to OpenZeppelin's [`SafeERC20`](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v4.5.0/contracts/token/ERC20/utils/SafeERC20.sol) library, which reverts on failure ([PR #54](https://github.com/eth-infinitism/account-abstraction/pull/54/files)).

> **Takeaway:** Always check ERC-20 transfer return values, or use `SafeERC20` to make failures revert automatically.

---

### Finding 3: Use of `transfer()` Is Potentially Unsafe

**Issue:** The `withdrawTo` function in `StakeManager` and the `transfer` function in `SimpleWallet` both used Solidity's built-in `transfer()` to send Ether. This function forwards a fixed 2300 gas stipend, which is [no longer considered safe](https://consensys.net/diligence/blog/2019/09/stop-using-soliditys-transfer-now/) — it can cause failures when interacting with contracts that need more gas in their `receive` / `fallback` functions.

**Fix:** Partially fixed by switching to `call` in `StakeManager` ([PR #57](https://github.com/eth-infinitism/account-abstraction/pull/57/files)). The `SimpleWallet` contract was left unchanged.

> **Takeaway:** Prefer `call{value: ...}("")` or OpenZeppelin's [`Address.sendValue()`](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v4.5.0/contracts/utils/Address.sol#L60) over Solidity's `transfer()`. Always follow the **checks-effects-interactions** pattern.

---

### Reference

- [OpenZeppelin — EIP-4337 Account Abstraction Audit](https://blog.openzeppelin.com/eth-foundation-account-abstraction-audit/)

## 2026 Update Note

- This post was migrated from the original blog and language-polished in 2026.
- EIP-4337 has since been deployed on Ethereum mainnet and is widely used for smart account wallets. The security patterns discussed here — SafeERC20, avoiding `transfer()`, msg.sender checks — remain essential Solidity best practices.
