---
title: "Open-Channel SSD Series (1): LightNVM Paper Review"
date: 2017-08-13 10:00:00 +0900
categories: [Research, Open-Channel SSD]
tags: [open-channel-ssd, lightnvm, nand-flash, pblk, linux-kernel, ssd, ftl]
description: "Reading notes on the FAST'17 paper — LightNVM: The Linux Open-Channel SSD Subsystem. Covers NAND management, the PPA I/O interface, pblk architecture, and experimental evaluation."
---

> Paper: Bjørling, M., González, J., & Bonnet, P. "LightNVM: The Linux Open-Channel SSD Subsystem." *FAST'17*, pp. 359–374.

## Abstract

Conventional SSDs hide their internal geometry behind a block I/O interface, leading to **unpredictable latency** and inefficient resource utilization. LightNVM is the first open, generic Linux subsystem for **Open-Channel SSDs** — devices that expose their internal layout to the host operating system so that flash management (address translation, garbage collection, wear leveling, etc.) can be handled in software. The paper demonstrates that LightNVM achieves high throughput while providing the knobs to control I/O latency variability.

## 1. Introduction

Modern SSD shortcomings are **not** caused by hardware limitations. The non-volatile memory chips inside SSDs deliver predictable, high-performance I/O — the problems arise from how tens of chips are managed behind a legacy block interface originally designed for magnetic disks.

**Open-Channel SSDs** address this by exposing internal geometry to the host. Two major concerns follow:

1. A block-device abstraction built on top of an open-channel SSD must still deliver **high performance**.
2. Design choices and **trade-off opportunities** (throughput vs. latency vs. endurance) must be clearly identified.

The paper makes four contributions:

1. Characterization of open-channel SSD management concerns.
2. The **Physical Page Address (PPA)** I/O interface — a hierarchical address space with vectored data commands.
3. **LightNVM** — the Linux subsystem for open-channel SSD management.
4. An evaluation on a first-generation open-channel SSD showing high performance and tunable latency.

## 2. Open-Channel SSD Management

### 2.1 NAND Flash Characteristics

NAND flash cells are connected **in series** with no address lines, so operations are line-aligned:

| Operation | Granularity |
|-----------|-------------|
| Read      | Page        |
| Write     | Page        |
| Erase     | Block       |

Even reading a single byte requires reading the **entire page** containing it. Likewise, modifying a single byte requires erasing the whole block and rewriting every page — the Flash Translation Layer (FTL) and **wear leveling** are designed to mitigate this cost.

#### SLC / MLC / TLC

| Type | Bits per Cell | Examples         |
|------|:------------:|------------------|
| SLC  | 1            | 0, 1             |
| MLC  | 2            | 00, 01, 10, 11   |
| TLC  | 3            | 000 … 111        |

Performance and endurance rank **SLC > MLC > TLC**, while cost-per-bit is the reverse. For the same die area, MLC offers 2× and TLC 3× the capacity of SLC.

### 2.2 Managing NAND

#### Write Buffering

When the host sector size (e.g., 4 KB) is smaller than the NAND page size (e.g., 16 KB), **write buffering** is necessary. Sector writes are buffered until enough data accumulates to fill a flash page; padding is applied when a flush is forced.

- **Host-side buffer**: Writes are acknowledged immediately on cache hit; the downside is potential data loss on power failure.
- **Device-side buffer (CMB)**: Supports small writes efficiently but needs extra controller logic and power capacitors for durability.

#### Error Handling

- **ECC** (BCH / LDPC) — applied per sector, stored in the page's out-of-band area.
- **BER management** — vendors may tune NAND threshold voltages to keep Bit Error Rate below a threshold; read-hot / write-cold blocks are rewritten proactively.
- **Write failure** — recovery is needed at the block level; already-written pages must be read back.
- **Erase failure** — the block is simply marked bad; no retry.

### 2.3 Lessons Learned

1. **Device warranty requires PE-cycle management** — PE cycles must be tracked on the device.
2. **Exposing raw media characterization to the host is inefficient** — it limits media abstraction.
3. **Write-buffer placement is use-case-dependent** — host-side eliminates device DRAM needs; device-side supports durability for small writes.
4. **Application-agnostic wear leveling is mandatory** — free blocks must be selected considering (i) bad blocks, (ii) dynamic wear leveling via PE counts, and (iii) static wear leveling by migrating cold data.

### 2.4 Architecture

The architecture separates *media-specific* concerns (handled by the device) from *workload-specific* concerns (handled by the host).

## 3. Physical Page Address (PPA) I/O Interface

### 3.1 Address Space

- **SSD Architecture**: Channels → Parallel Units (PUs / LUNs) → Dies. Each PU processes one I/O at a time.
- **Media Architecture**: PU → Blocks → Pages (minimum transfer unit) → Sectors (minimum ECC unit).

#### NAND Flash Memory Example

A sample 8 GB (64 Gb) NAND chip with **2 dies × 2 planes**:

| Level | Count         |
|-------|---------------|
| Plane | 1,024 Blocks  |
| Block | 256 Pages     |
| Page  | 8 KB          |

> The paper assumes each PU maps to **one physical NAND die**.

PPA encoding makes it efficient to perform operations like "get next page on the next channel" via simple **bit-shifting**.

### 3.2 Geometry and Management

For the host to control the SSD, an open-channel SSD exposes four properties:

1. **Geometry** — dimensions of the PPA address space (channels, PUs, planes, blocks, pages, sectors, OOB size).
2. **Performance** — typical/max latency for read, write, erase; max in-flight commands per channel.
3. **Media-specific metadata** — NAND type, multi-plane support, page pairing info, etc.
4. **Controller capabilities** — write buffering, failure handling, RAID configuration, over-provisioning strategy.

> **Over-provisioning**: Wear leveling and GC require free space to operate smoothly, so a hidden reserve is maintained beyond the user-visible capacity.

### 3.3 Read / Write / Erase

**Vectored I/Os** apply a single command to a **vector of addresses**, exploiting the SSD's internal parallelism. For example, 64 KB of data (sixteen 4 KB sectors) can be striped across 16 addresses in one write command.

Three command models were evaluated: (i) NVMe I/O commands, (ii) grouped I/Os, (iii) **Vectored I/Os** — the chosen approach, requiring an extra DMA for the PPA list.

## 4. LightNVM

### 4.1 Architecture

LightNVM is the open-channel SSD subsystem in Linux, layered as:

1. **NVMe Device Driver** — provides kernel modules access to open-channel SSDs through the PPA I/O interface.
2. **LightNVM Subsystem** — manages device geometry, provisioning, and I/O dispatch.
3. **High-Level I/O Interface** — exposes open-channel SSDs to kernel modules and user-space applications.

### 4.2 pblk — The Physical Block Device

**pblk** is a fully associative, host-based FTL within LightNVM. Its responsibilities:

1. Handle controller- and media-specific constraints (e.g., buffering until a full flash page can be programmed).
2. Map logical addresses to physical addresses at **4 KB granularity** and maintain L2P table integrity.
3. Handle errors.
4. Implement **garbage collection (GC)**.
5. Handle flushes (padding partial pages, honoring `fsync`).

#### 4.2.2 Mapping-Table Recovery

L2P consistency is maintained via three redundancy mechanisms:

1. **Snapshot** — full L2P copy on power-down; periodic checkpoint FTL logs recording block allocate/erase operations.
2. **Block-level metadata** — first page stores a block sequence number + pointer to the previous block; last pages store the relevant L2P fragment, the same sequence number, and a pointer to the next block.
3. **Per-page OOB** — a portion of the L2P is embedded in the out-of-band area of every written page.

#### 4.2.3 Error Handling

Unlike a traditional FTL, **pblk handles only write and erase errors** — read-error recovery is delegated to upper layers.

- **Write failure** → two recovery mechanisms are initiated.
- **Erase failure** → the block is marked bad immediately; since no data was written, no recovery is needed.

#### 4.2.4 Garbage Collection

pblk tracks a **valid-page count** per block and recycles the block with the fewest valid sectors. The reverse L2P mapping for a block is obtained from the partial L2P stored on its last pages (exploiting the fact that recycled blocks are fully written).

A **PID-controlled rate limiter** prevents user I/Os from interfering with GC; the feedback loop is driven by the total number of free blocks available.

## 5. Experimental Evaluation

The evaluation covers sanity checks and uniform workloads, demonstrating that LightNVM delivers high throughput while exposing the controls needed to tune latency.

---

### Reference

Bjørling, M., González, J., & Bonnet, P. (2017, February). LightNVM: The Linux Open-Channel SSD Subsystem. In *FAST* (pp. 359–374).

## 2026 Update Note

- This post was migrated from the original blog and language-polished in 2026.
- While the specific LightNVM / pblk subsystem has since been superseded by newer kernel abstractions (e.g., the NVMe Zoned Namespace spec), the core concepts — host-managed flash, PPA addressing, and host-side FTL — remain foundational to modern computational-storage and ZNS SSD research.
