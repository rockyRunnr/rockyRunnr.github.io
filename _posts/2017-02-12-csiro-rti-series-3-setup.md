---
title: "CSIRO RTI Series (3): Contiki + CC2650 Setup on Linux"
date: 2017-02-12 10:01:50 +0900
categories: [Research, RTI]
tags: [contiki, cc2650, linux, setup]
image:
  path: /assets/img/posts/csiro/csiro_6_1.png
description: "A practical setup guide for building and flashing Contiki apps to CC2650 boards on Linux."
---

## Setup: Contiki with CC2650 on Linux

This guide assumes:

- Linux environment (originally tested on Ubuntu 14.04)
- `root`/sudo access

Clone examples/tools from either repository:

- CSIRO examples: <https://github.com/csiro-wsn/contiki-examples>
- My mirror/fork: <https://github.com/generousRocky/radioTomography/tree/master/contiki-examples>

> At the time, I used my fork because the CSIRO script had a few typos in `tools/tools_install.sh`.

Install required 32-bit libraries (legacy toolchain dependencies):

```bash
sudo apt-get install libc6:i386 libx11-6:i386 libasound2:i386 libatk1.0-0:i386 \
  libcairo2:i386 libcups2:i386 libdbus-glib-1-2:i386 libgconf-2-4:i386 \
  libgdk-pixbuf2.0-0:i386 libgtk-3-0:i386 libice6:i386 libncurses5:i386 \
  libsm6:i386 liborbit2:i386 libudev1:i386 libusb-0.1-4:i386 libstdc++6:i386 \
  libxt6:i386 libxtst6:i386 libgnomeui-0:i386 libusb-1.0-0-dev:i386 \
  libcanberra-gtk-module:i386 gtk2-engines-murrine:i386 unzip
```

Then install the toolchain via script and build:

```bash
make TARGET=srf06-cc26xx BOARD=sensortag/cc2650
```

To flash `.elf` binaries to CC2650, use TI UniFlash:

- <http://www.ti.com/tool/uniflash>

If UniFlash reports a `libgcrypt.so.11` error, install a compatible `libgcrypt11` package.

After installation, update XDS110 firmware:

```bash
cd /opt/ti/uniflash_3.4/ccs_base/common/uscif/xds110/
./xdsdfu -m
./xdsdfu -f firmware.bin -r
```

This initializes the debug interface for first-time use.
