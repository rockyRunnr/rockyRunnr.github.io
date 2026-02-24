---
title: "CSIRO RTI Series (1): What Is Radio Tomographic Imaging?"
date: 2017-02-10 10:01:50 +0900
categories: [Research, CSIRO]
tags: [csiro-rti, rti, wireless-sensor-network, rssi, csiro]
image:
  path: /assets/img/posts/csiro/csiro_1_1.png
description: "Introduction to Radio Tomographic Imaging (RTI), project scope, and system overview."
---

## What is Radio Tomographic Imaging?

![RTI overview](/assets/img/posts/csiro/csiro_1_1.png){: width="420" }

Radio Tomographic Imaging (RTI) is a technique for imaging **passive objects** (objects without transmitters) by using a wireless network. The key signal is RSSI (Received Signal Strength Indicator). In general, RSSI changes when an object blocks or disturbs a radio path.

![RSSI change over time](/assets/img/posts/csiro/csiro_1_2.png){: width="450" }

The graph above shows RSSI variation over time. During experiments, RSSI fluctuated as a person moved around the nodes. In an RTI network, nodes generate RSSI data rapidly, and we reconstruct images from that data.

During my internship at CSIRO, I worked on building an RTI system using low-power sensor devices:

- **Device**: TI SensorTag CC2650
- **OS**: Contiki

The work had two main steps:

1. Build device applications for the sensor nodes.
2. Reconstruct images from collected network data.

I implemented:

- Node firmware for RTI network participants
- Master-node firmware for scheduling and collection

After deploying nodes around a target area, I collected per-link RSSI data and reconstructed area images.

The next posts cover the scheduling design and reconstruction details.

---

### Reference

[1] Wilson, Joey, and Neal Patwari. “Radio tomographic imaging with wireless networks.” *IEEE Transactions on Mobile Computing* 9.5 (2010): 621–632.


## 2026 Update Note

- This post was migrated from the original blog and language-polished in 2026.
- Core RTI concepts remain valid: passive sensing, RSSI-based attenuation tracking, and image reconstruction through link measurements.
- For modern replication, consider newer IoT stacks (e.g., Zephyr + nRF52/ESP32-class hardware) if Contiki/CC2650 toolchains are unavailable.
