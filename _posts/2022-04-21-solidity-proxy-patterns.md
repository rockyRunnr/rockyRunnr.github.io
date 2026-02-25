---
title: "Solidity Deep Dive (3): Proxy Patterns and Upgradable Contracts"
date: 2022-04-21 10:00:00 +0900
categories: [Development, Blockchain]
tags: [solidity, ethereum, proxy-pattern, upgradable-contract, openzeppelin, delegatecall]
description: "How Solidity proxy patterns enable upgradable smart contracts — fallback functions, delegatecall, unstructured storage, and storage collision prevention."
---

## Why Proxy Patterns?

The biggest limitation of Ethereum smart contracts is that **once deployed, their code cannot be modified**. Traditional centralized services receive continuous updates — new features, bug fixes, security patches — but the default Ethereum development model does not support this.

Proxy patterns make upgrades *partially* possible. The key idea:

1. A **proxy contract** serves as the user-facing entry point.
2. A separate **logic (implementation) contract** contains the actual business logic.
3. To upgrade, deploy a new logic contract and update the proxy to point to it.

## How It Works: Fallback + delegatecall

Two Solidity features make proxy contracts possible:

### Fallback Function

When a function that does **not exist** in a contract is called, the contract's **fallback function** is invoked instead:

```solidity
contract MyContract {
    fallback() external {
        // Called for any unknown function selector
    }
}
```

### delegatecall

A low-level function that executes another contract's code **in the context of the calling contract**. Storage changes are applied to the **proxy's** storage, not the logic contract's.

### Proxy Forwarding

Combining both, the proxy contract forwards every call to the logic contract (this is essentially what OpenZeppelin's proxy does):

```solidity
assembly {
    let ptr := mload(0x40)

    // (1) Copy incoming call data
    calldatacopy(ptr, 0, calldatasize())

    // (2) Forward call to logic contract via delegatecall
    let result := delegatecall(gas(), _impl, ptr, calldatasize(), 0, 0)
    let size := returndatasize()

    // (3) Retrieve return data
    returndatacopy(ptr, 0, size)

    // (4) Forward return data back to caller
    switch result
    case 0 { revert(ptr, size) }
    default { return(ptr, size) }
}
```

For a detailed explanation of this assembly code, see OpenZeppelin's [Proxy Patterns](https://blog.openzeppelin.com/proxy-patterns/) and [Proxy Upgrade Pattern](https://docs.openzeppelin.com/upgrades-plugins/1.x/proxies) documentation.

## Writing Upgradable Contracts with OpenZeppelin

Because the proxy calls the logic contract via `delegatecall`, **constructors cannot be used** — they execute only once at deployment and cannot be proxied. Instead, use a regular `initialize` function:

```solidity
contract MyContract {
    uint256 public x;

    function initialize(uint256 _x) public {
        x = _x;
    }
}
```

Since regular functions can be called multiple times, OpenZeppelin provides the `Initializable` contract with an `initializer` modifier that enforces single-execution.

### Initializing Inherited Contracts

Constructors automatically invoke parent constructors, but `initialize` functions do not. You must **explicitly call** base contract initializers:

```solidity
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";

contract BaseContract is Initializable {
    uint256 public y;

    function initialize() public initializer {
        y = 42;
    }
}

contract MyContract is BaseContract {
    uint256 public x;

    function initialize(uint256 _x) public initializer {
        BaseContract.initialize(); // Don't forget this!
        x = _x;
    }
}
```

## Unstructured Storage Proxies

Storage variables live in the **proxy contract** (due to `delegatecall`). However, the proxy itself needs an `_implementation` address variable. If stored in slot 0, it would **collide** with the logic contract's first storage variable.

OpenZeppelin's **unstructured storage** pattern solves this by storing `_implementation` in a **pseudo-random slot** (derived from a hash). With 2²⁵⁶ possible slots, the collision probability is negligible.

## Storage Collisions Between Implementation Versions

Even without the `_implementation` collision, upgrading to a new logic contract version can cause collisions if you:

- **Insert** a new variable in the middle of existing declarations
- **Reorder** existing variables

New storage variables must always be **appended** — never inserted or reordered.

---

### References

1. [OpenZeppelin — Proxy Upgrade Pattern](https://docs.openzeppelin.com/upgrades-plugins/1.x/proxies)
2. [OpenZeppelin — Upgrading Smart Contracts](https://docs.openzeppelin.com/learn/upgrading-smart-contracts)
3. [OpenZeppelin — Writing Upgradeable Contracts](https://docs.openzeppelin.com/upgrades-plugins/1.x/writing-upgradeable)

## 2026 Update Note

- This post was migrated from the original blog and language-polished in 2026.
- OpenZeppelin's proxy architecture has matured significantly since 2022 (UUPS vs. Transparent Proxy, EIP-1967 storage slots, Beacon Proxies). The core concepts described here remain valid.
