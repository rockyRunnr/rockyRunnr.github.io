---
title: "IsoKV: An Isolation Scheme for Key-Value Stores Exploiting SSD Internal Parallelism (HiPC'19)"
date: 2019-12-31 10:00:00 +0900
categories: [Research, Database]
tags: [isokv, rocksdb, open-channel-ssd, nvme, key-value-store, hipc, garbage-collection]
image:
  path: /assets/img/posts/research/hipc.png
description: "Paper accepted at IEEE HiPC 2019 — IsoKV isolates key-value store I/O by exploiting SSD internal parallelism to reduce interference and eliminate garbage collection overhead."
---

## Abstract

Modern data centers aim to leverage the high parallelism in storage devices for I/O-intensive applications such as storage servers, cache systems, and key-value stores. Key-value stores, in particular, must deliver **highly reliable service with high performance**.

To increase I/O performance, many data centers have adopted **NVMe-based SSDs**, which are characterized by a high degree of parallelism. However, they may not guarantee **predictable performance** when handling heavily mixed read and write requests — interference between application I/O and internal operations (e.g., Garbage Collection) can degrade both throughput and response time.

**IsoKV** is an isolation scheme for key-value stores that **exploits internal parallelism in SSDs** to minimize this interference:

- IsoKV manages the SSD's level of parallelism directly through an **application-driven flash management scheme**.
- By storing data with different characteristics in **dedicated internal parallel units** of the SSD, IsoKV reduces interference between I/O requests.
- IsoKV **synchronizes LSM-tree logic with SSD data management** to eliminate garbage collection entirely.

We implemented IsoKV on **RocksDB** and evaluated it using an **Open-Channel SSD**. Experiments show that IsoKV improves:

- **Overall throughput** by an average of **1.20×**
- **Response time** by an average of **43%**

compared to the existing scheme.

---

## Paper Link

IEEE Xplore: [IsoKV: An Isolation Scheme for Key-Value Stores by Exploiting Internal Parallelism in SSD](https://ieeexplore.ieee.org/document/8990456)

---

## 2026 Update Note

- This post was migrated from the original blog and language-polished in 2026.
- The IsoKV concept of isolating workloads across SSD parallel units has influenced later work in ZNS-aware key-value stores, where zone-level isolation achieves similar interference reduction without requiring an open-channel SSD.
