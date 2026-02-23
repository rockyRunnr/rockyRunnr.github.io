---
title: "CSIRO RTI Series (4): Device Application and Scheduling Design"
date: 2017-02-14 10:01:50 +0900
categories: [Research, CSIRO]
tags: [csiro-rti, contiki, scheduling, rssi, firmware]
image:
  path: /assets/img/posts/csiro/csiro_4_1.png
description: "Master-node scheduling and collision avoidance design for RSSI-based RTI."
---

## Device Application Design for RTI

There are two firmware roles in this RTI system:

1. **Normal node**: broadcasts packets and measures RSSI.
2. **Master node**: schedules nodes and collects raw RSSI data.

The master sends command packets to control each node’s broadcast interval and iteration count.

A key challenge is **radio interference**. RTI heavily relies on RSSI quality, so simultaneous transmissions can corrupt measurements. To avoid this, I introduced a **time-slot schedule** where only one node broadcasts in each slot.

Example schedule (N=5 nodes, iteration=3):

![RTI scheduling](/assets/img/posts/csiro/csiro_4_1.png){: width="800" }

In each slot:

- The master issues a command (control plane)
- The selected node broadcasts 3 times (data plane)
- Payload includes RSSI summaries from the previous cycle

Example payload:

```text
N 3 -46 -45 -43 0 -43
```

Meaning:

- `N`: normal packet type
- `3`: node ID
- Remaining values: average RSSI from each peer
- `0`: self-link placeholder (node3 → node3)

Source code (original project):

- Normal node: <https://github.com/generousRocky/radioTomography/tree/master/contiki-examples/radio_tomography>
- Master node: <https://github.com/generousRocky/radioTomography/tree/master/contiki-examples/rti_mater>


## 2026 Update Note

- Migrated and language-polished in 2026.
- The time-slot scheduling design is still the key practical lesson: measurement quality collapses when concurrent transmissions are not controlled.
- This approach can be generalized to other low-power sensing networks where signal quality is central to inference.
