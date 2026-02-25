---
title: "Open-Channel SSD Series (6): liblightnvm — User-Space Open-Channel SSD Control"
date: 2018-02-20 10:00:00 +0900
categories: [Research, Open-Channel SSD]
tags: [open-channel-ssd, lightnvm, liblightnvm, user-space, nand-flash, vectorized-io]
description: "Overview of liblightnvm, a user-space library for direct physical flash I/O on Open-Channel SSDs — device geometry, physical addressing, vectorized I/O constraints, and virtual blocks."
---

## What Is liblightnvm?

**liblightnvm** is a user-space library for managing provisioning and I/O submission to physical flash on Open-Channel SSDs. It enables I/O-intensive applications to implement their own Flash Translation Layers (FTLs) using application-level data structures.

The design philosophy is that high-performance I/O applications often use structures that resemble FTL internals — for example, Log-Structured Merge Trees (LSMs), which manage data placement and garbage collection. Popular key-value stores like **RocksDB**, **MongoDB**, and **Apache Cassandra** all use LSM variants. These applications can benefit from a **direct path to physical flash**, bypassing the multiple indirection layers of the traditional I/O stack (page cache → VFS → file system → device L2P table).

liblightnvm exposes **append-only primitives** via direct physical flash access to support this class of applications.

> GitHub: <https://github.com/OpenChannelSSD/liblightnvm>

## Obtaining Device Information

Use the following command to retrieve the physical geometry of an Open-Channel SSD:

```bash
nvm_dev info /dev/nvme0n1
```

Example output:

```yaml
dev:
  verid: 0x02
  be_id: 0x02
  name: 'nvme0n1'
  path: '/dev/nvme0n1'
  fd: 3
  ssw: 12
  pmode: 'DUAL'
  erase_naddrs_max: 64
  read_naddrs_max: 64
  write_naddrs_max: 64
  meta_mode: 0
  bbts_cached: 0
dev_geo:
  nchannels: 16
  nluns: 8
  nplanes: 2
  nblocks: 1020
  npages: 512
  nsectors: 4
  page_nbytes: 16384
  sector_nbytes: 4096
  meta_nbytes: 16
  tbytes: 2190433320960
  tmbytes: 2088960
dev_ppaf:
  ch_off: 25, ch_len: 04
  lun_off: 22, lun_len: 03
  pl_off: 02, pl_len: 01
  blk_off: 12, blk_len: 10
  pg_off: 03, pg_len: 09
  sec_off: 00, sec_len: 02
```

## Physical Addressing

Physical page addresses are represented by a `struct nvm_addr`. You can construct an address from geometry coordinates:

```bash
# Sector 3, page 10, block 200, plane 0, LUN 1, channel 4
nvm_addr from_geo /dev/nvme0n1 4 1 0 200 10 3
```

Output:

```
0x04010003000a00c8: {ch: 04, lun: 01, pl: 0, blk: 0200, pg: 010, sec: 3}
```

## Vectorized I/O

liblightnvm supports vectorized I/O — submitting multiple addresses in a single command to exploit the SSD's internal parallelism.

### Write Constraints

| # | Constraint | Details |
|---|-----------|---------|
| 1 | **Erase before write** | Blocks must be erased before they can be written. |
| 2 | **Full-page granularity** | Writes must fill at least one complete flash page. |
| 3 | **Contiguous within a block** | Pages must be written sequentially within a block. |
| 4 | **All-plane writes** (minimum write) | When a die has two planes, **both planes must be written together**. Either satisfy this constraint or disable plane-mode. |
| 5 | **64 addresses per command** (maximum write) | A single NVMe command can address up to 64 PPAs, allowing up to 4 KB × 64 = 256 KB per write command. |

### Read Constraints

| # | Constraint | Details |
|---|-----------|---------|
| 1 | **Single-sector granularity** | Reads operate at the sector level and can be non-contiguous. |
| 2 | **Block must be closed** | A block can only be read after **all pages** within it have been written (i.e., the block is closed). |

## Virtual Blocks

To reduce the cognitive overhead of managing NAND constraints, liblightnvm introduces a **virtual block** abstraction. A virtual block behaves like a physical block — the same NAND media constraints apply — but it encapsulates:

- Command and address construction for **parallel vectorized I/O**
- A **flat address space** that can be read/written using semantics equivalent to libc's `read`/`write` primitives

This abstraction lets application developers work with open-channel SSDs without directly managing the complexity of multi-plane addressing and vectorized command construction.

---

## 2026 Update Note

- This post was migrated from the original blog and language-polished in 2026.
- liblightnvm has since been superseded. For modern user-space flash access, consider the **xNVMe** library, which provides a unified interface for NVMe devices including ZNS SSDs.
