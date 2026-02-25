---
title: "Open-Channel SSD Series (6): Write Buffer and Thread Configuration — Performance Analysis (KSC 2017)"
date: 2018-02-01 10:00:00 +0900
categories: [Research, Open-Channel SSD]
tags: [open-channel-ssd, lightnvm, pblk, performance, fio, write-buffer, multi-thread, ksc]
description: "Performance analysis of write buffer sizing and I/O thread configuration on an Open-Channel SSD platform using the CNEX Labs Westlake SDK — presented at KSC 2017."
---

## Abstract

An Open-Channel SSD delegates flash management to the host operating system instead of implementing an on-device Flash Translation Layer (FTL). Linux provides the **LightNVM** abstraction layer for this purpose, and **pblk** (the Physical Block Device) is a kernel module sitting within LightNVM that performs FTL functions — address translation, garbage collection, and write buffering — on the host side.

This paper examines how write requests are processed in an Open-Channel SSD environment and presents **performance analysis results** based on:

1. The **write buffer size** configured in pblk.
2. The **thread configuration** for I/O requests.

## Introduction

SSDs are expected to become the dominant storage medium in the coming years. While they offer superior performance over traditional HDDs, they still suffer from inefficient resource utilization [4], **long tail latency**, and **unpredictable I/O latency** [1, 2, 3] — problems largely caused by the legacy Block I/O interface optimized for HDDs [5].

**Open-Channel SSDs** solve these issues by exposing internal SSD geometry to the host OS, allowing the host to manage physical data placement and I/O scheduling directly. The host and SSD controller **share responsibility** for device operations [3], with address translation, garbage collection, and error handling moved to the host side. This lets applications tailor the storage software stack to their specific workload patterns.

- **LightNVM** has been included in the Linux kernel since version 4.4.
- **pblk** has been included since kernel 4.12, providing host-side FTL functionality.

## Experimental Setup and Evaluation

The experiments had two goals:

1. **Analyze I/O performance as a function of write buffer size** — varying the number of entries in pblk's software write buffer.
2. **Analyze performance scaling with I/O thread count** — measuring behavior under multi-core, multi-threaded workloads.

### Hardware and Software Configuration

| Component | Specification |
|-----------|--------------|
| CPU | Intel Xeon E7-8870 (72 cores) |
| DRAM | 16 GiB |
| Interface | PCIe 3.0 |
| SSD | CNEX Labs Westlake SDK (2 TB NAND MLC Flash) |
| OS | Ubuntu 16.04.3 LTS Server |
| Kernel | Linux 4.14.0-rc2 with pblk |
| Benchmark | fio [6] |

All experiments bypassed the file system (raw device I/O), were repeated **3 times** under identical conditions, and averaged. The number of active CPU cores matched the I/O thread count. Write buffer size was controlled by adjusting the number of buffer entries.

## Conclusion

**Read performance** scaled proportionally with thread count up to a point, after which the rate of improvement diminished. Notably, increasing read threads from 54 to 72 produced almost no performance change.

**Read performance vs. write buffer size** showed a consistent improvement rate regardless of thread count — larger buffers increased the buffer cache hit ratio for read requests.

**Write performance** with buffer sizes ≥ 64 MB showed a slight gain when threads increased from 2 to 4, but minimal improvement beyond that. With a 32 MB buffer, random write performance scaled significantly up to 18 threads.

At 32 MB buffer size, both sequential and random write performance **dropped sharply beyond 18 threads** compared to the 18-thread configuration. This suggests that with a smaller buffer and many writer threads, the buffer becomes perpetually full, eliminating any parallelism benefit.

Overall, write performance gains from additional threads and larger buffers were **much smaller** than read performance gains. Future work will investigate the root causes of write-path bottlenecks and strategies to increase parallelism.

---

### References

[1] Hao, M. et al. (2016). The Tail at Store: A Revelation from Millions of Hours of Disk and SSD Deployments. *FAST*, pp. 263–276.

[2] Chen, F. et al. (2011). CAFTL: A Content-Aware Flash Translation Layer Enhancing the Lifespan of Flash Memory based Solid State Drives. *FAST*, Vol. 11, pp. 77–90.

[3] Bjørling, M. et al. (2017). LightNVM: The Linux Open-Channel SSD Subsystem. *FAST*, pp. 359–374.

[4] Agrawal, N. et al. (2008). Design Tradeoffs for SSD Performance. *USENIX ATC*, Vol. 8, pp. 57–70.

[5] Swanson, S. & Caulfield, A. M. (2013). Refactor, Reduce, Recycle: Restructuring the I/O Stack for the Future of Storage. *Computer*, 46(8), 52–59.

[6] Axboe, J. Fio — Flexible I/O Tester. <http://freecode.com/projects/fio> (2014).

---

## 2026 Update Note

- This post was migrated from the original blog and language-polished in 2026.
- The original paper was presented at the Korea Software Congress (KSC) 2017.
- The write-buffer and thread-scaling observations remain relevant to modern host-managed flash architectures, including ZNS SSDs that face similar write-path bottlenecks at high parallelism.
