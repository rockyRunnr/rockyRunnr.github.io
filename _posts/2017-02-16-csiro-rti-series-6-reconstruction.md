---
title: "CSIRO RTI Series (6): Image Reconstruction"
date: 2017-02-16 10:01:50 +0900
categories: [Research, RTI]
tags: [image-reconstruction, rssi, inverse-problem]
image:
  path: /assets/img/posts/csiro/csiro_6_0.png
description: "Reconstruction model and comparison of three RSSI-derived y-vector strategies."
---

## Image Reconstruction

[![RTI demo video](/assets/img/posts/csiro/csiro_6_0.png){: width="700" }](https://www.youtube.com/watch?v=A1ZUN6HhKXg)

I followed the core reconstruction concept from:

> Wilson & Patwari, *Radio tomographic imaging with wireless networks* [1]

The model links RSS-based measurements to an attenuation image:

![Equation 1](/assets/img/posts/csiro/csiro_6_2.gif){: width="600" }

![Equation 2](/assets/img/posts/csiro/csiro_6_3.png){: width="600" }

Where:

- **y**: vector of RSS measurement differences
- **W**: weighting matrix
- **x**: attenuation image to estimate (in dB)
- **Cₓ**: prior covariance matrix
- **σₙ⁻²**: node variance term

I skip the full derivation (well covered in the paper) and focus on how I defined **y** in practice.

## Three y-vector strategies

### 1) Cycle-to-cycle difference: \(T_n - T_{n-1}\)

- Best spatial accuracy during continuous movement
- Weakness: when an object stops moving, it can fade from the image as the network adapts

### 2) Baseline difference: \(T_n - T_0\)

- Better for detecting slow or static objects
- Weakness: baseline drifts with environmental changes, so long runs become less reliable

### 3) Standard deviation-based y

- Similar quality to method 1
- Improved as iteration count increased

## Conclusion

I used **method 1** as the default because it gave the most stable overall results in my setup. Methods 2 and 3 are still useful alternatives depending on environment stability and runtime conditions.

---

### Reference

[1] Wilson, Joey, and Neal Patwari. “Radio tomographic imaging with wireless networks.” *IEEE Transactions on Mobile Computing* 9.5 (2010): 621–632.
