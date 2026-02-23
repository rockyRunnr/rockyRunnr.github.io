---
title: "CSIRO RTI Series (2): TI CC2650 + Contiki Platform"
date: 2017-02-11 10:01:50 +0900
categories: [Research, CSIRO]
tags: [csiro-rti, cc2650, contiki, low-power, wireless-sensor-network]
image:
  path: /assets/img/posts/csiro/csiro_2_1.png
description: "Why TI SensorTag CC2650 and Contiki were selected for low-power RTI development."
---

In this RTI project, I used the **TI CC2650 SensorTag** and implemented the node applications on **Contiki OS**. The goal was to build a practical RTI pipeline on low-power devices.

## TI SensorTag CC2650

![TI CC2650 SensorTag](/assets/img/posts/csiro/csiro_2_1.png){: width="600" }

The CC2650 targets low-power wireless applications such as Bluetooth Smart, ZigBee, and 6LoWPAN. Its low active and sleep currents make it suitable for battery-powered sensing systems.

## Contiki OS

Contiki is an open-source operating system for IoT devices. It is designed for constrained hardware and provides a practical environment for building wireless sensor networks.

---

### References

1. TI, *Multi-Standard CC2650 SensorTag Design Guide*  
   <http://www.ti.com/lit/ug/tidu862/tidu862.pdf>
2. Contiki OS  
   <http://www.contiki-os.org>


## 2026 Update Note

- Migrated and language-polished in 2026.
- Hardware/OS choices reflect the project period; today, equivalent low-power platforms can be substituted without changing the RTI architecture.
- This post is kept as a design record of platform decisions made during the original CSIRO internship project.
