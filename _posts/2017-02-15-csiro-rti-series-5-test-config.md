---
title: "CSIRO RTI Series (5): Test Configuration"
date: 2017-02-15 10:01:50 +0900
categories: [Research, CSIRO]
tags: [csiro-rti, experiment, configuration, voxel, deployment]
image:
  path: /assets/img/posts/csiro/csiro_5_1.png
description: "Node deployment and reconstruction parameters used for RTI experiments."
---

## Test Configuration

### Node deployment

![Node deployment](/assets/img/posts/csiro/csiro_5_1.png){: width="500" }

Nodes were deployed from top-left to bottom-right as shown above.

### Node configuration

```text
NUM_OF_NODE = 20
NUM_OF_LINK = 20*19 = 380
NUM_OF_ONESIDE = 6
```

### Reconstruction configuration

```text
ROW = 25
NUM_OF_VOXEL = 25*25 = 625
NORMALIZED_PIXEL_WIDTH = 0.984
WIDTH_OF_WEIGHTING_ELLIPSE = 0.02
PIXEL_CORRELATION_CONSTANT = 3
PIXEL_VARIANCE = 0.4
```

> Note: The original draft had small typos (`RAW`, `WITH`, and `381` links). They are corrected here for readability and consistency.


## 2026 Update Note

- Migrated and language-polished in 2026.
- Minor notation/typo fixes were applied (e.g., link count and parameter names) for consistency.
- Parameter values are retained as experiment records and may require re-tuning for different physical layouts.
