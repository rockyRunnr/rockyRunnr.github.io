---
title: "Open-Channel SSD Series (3): pblk Read Path — Kernel Code Analysis"
date: 2017-08-20 10:00:00 +0900
categories: [Research, Open-Channel SSD]
tags: [open-channel-ssd, lightnvm, pblk, linux-kernel, kernel-code, read-path]
image:
  path: /assets/img/posts/ocssd/openChannelSSD.png
description: "Kernel source code walkthrough of the pblk read path in the LightNVM Open-Channel SSD subsystem — from bio submission to block-layer dispatch."
---

> Related paper: Bjørling et al., "LightNVM: The Linux Open-Channel SSD Subsystem," *FAST'17*.

## pblk: Physical Block Device Target

pblk implements a fully associative, host-based FTL that exposes a traditional block I/O interface. Its primary responsibilities are:

- Map logical addresses onto physical addresses (4 KB granularity) in an L2P table.
- Maintain L2P table integrity and support recovery from normal shutdown and power outage.
- Deal with controller- and media-specific constraints.
- Handle I/O errors.
- Implement garbage collection.
- Maintain consistency across synchronization points in the I/O stack.

For more information: <http://lightnvm.io>

## Source Code Overview

Most of LightNVM's core functionality is implemented in `drivers/lightnvm/` within the kernel source tree. Key files:

| File | Purpose |
|------|---------|
| `pblk.h` | Main header for the pblk target |
| `rrpc.h`, `rrpc.c` | Round-robin page-based hybrid FTL |
| `pblk-cache.c` | pblk's write cache |
| `pblk-core.c` | Core functionality |
| `pblk-gc.c` | Garbage collector |
| `pblk-init.c` | Initialization |
| `pblk-map.c` | LBA → PPA mapping strategy |
| `pblk-rb.c` | Write ring buffer |
| `pblk-read.c` | **Read path** |
| `pblk-recovery.c` | Recovery path |
| `pblk-rl.c` | Rate limiter for user I/O |
| `pblk-sysfs.c` | sysfs interface |
| `pblk-write.c` | Write path (buffer → media) |

NVMe block device creation is implemented in `core.c`. The FTL functions (write buffering, address mapping, garbage collection) reside in the `pblk-*` files.

## Read Path Overview

The read path starts when the file system submits a bio. The entry point is `pblk_make_rq`, which is registered as the `make_rq` callback:

```c
static blk_qc_t pblk_make_rq(struct request_queue *q, struct bio *bio)
{
    ...
    switch (pblk_rw_io(q, pblk, bio)) {
        ...
    }
}
```

---

`pblk_rw_io` dispatches reads and writes to their respective handlers:

```c
static int pblk_rw_io(struct request_queue *q, struct pblk *pblk,
                       struct bio *bio)
{
    if (bio_data_dir(bio) == READ) {
        ...
        ret = pblk_submit_read(pblk, bio);
        ...
        return ret;
    }

    // else → write path
    ...
}
```

---

### pblk_submit_read

This function builds an `nvm_rq` structure (containing the bio and PPA addresses), performs **LBA → PPA translation**, and submits the read I/O:

```c
int pblk_submit_read(struct pblk *pblk, struct bio *bio)
{
    ...
    // Build the rqd structure (bio + ppa)

    // LBA to PPA translation
    if (nr_secs > 1)
        pblk_read_ppalist_rq(pblk, rqd, blba, &read_bitmap);
    else
        pblk_read_rq(pblk, rqd, blba, &read_bitmap);
    ...
    ret = pblk_submit_read_io(pblk, rqd);
}
```

---

### Address Translation (L2P Lookup)

Both `pblk_read_ppalist_rq` and `pblk_read_rq` call `pblk_lookup_l2p_seq` to translate logical addresses. **If the data is found in the write buffer (cache), it is read from there directly**:

```c
pblk_read_ppalist_rq(pblk, rqd, blba, &read_bitmap)
{
    ...
    // LBA → PPA translation
    pblk_lookup_l2p_seq(pblk, &ppa, lba, 1);
    ...
    // If data is in the write buffer, read from cache
    if (pblk_addr_in_cache(ppa)) {
        if (!pblk_read_from_cache(pblk, bio, lba, ppa, 0, 1)) {
            pblk_lookup_l2p_seq(pblk, &ppa, lba, 1);
            goto retry;
        }
    } else {
        rqd->ppa_addr = ppa;
    }
    ...
}
```

---

The L2P table is accessed under a **spin lock** to ensure thread safety:

```c
void pblk_lookup_l2p_seq(struct pblk *pblk, struct ppa_addr *ppas,
                          u64 *lba_list, int nr_secs)
{
    ...
    spin_lock(&pblk->trans_lock);
    for (i = 0; i < nr_secs; i++) {
        lba = lba_list[i];
        ...
        ppas[i] = pblk_trans_map_get(pblk, lba);
    }
    spin_unlock(&pblk->trans_lock);
}
```

---

### pblk_trans_map_get

The `trans_map` inside the pblk structure holds the L2P mapping table. This function returns the physical page address for a given logical block address:

```c
static inline struct ppa_addr pblk_trans_map_get(struct pblk *pblk,
                                                  sector_t lba)
{
    struct ppa_addr ppa;

    if (pblk->ppaf_bitsize < 32) {
        u32 *map = (u32 *)pblk->trans_map;
        ppa = pblk_ppa32_to_ppa64(pblk, map[lba]);
    } else {
        struct ppa_addr *map = (struct ppa_addr *)pblk->trans_map;
        ppa = map[lba];
    }

    return ppa;
}
```

---

### I/O Submission

After translation, the I/O is submitted through the NVMe stack:

```c
static int pblk_submit_read_io(struct pblk *pblk, struct nvm_rq *rqd)
{
    ...
    err = pblk_submit_io(pblk, rqd);
    ...
}
```

`pblk_submit_io` checks for bad PPAs (under a spin lock) and then calls:

```c
int pblk_submit_io(struct pblk *pblk, struct nvm_rq *rqd)
{
    ...
    for (i = 0; i < rqd->nr_ppas; i++) {
        spin_lock(&line->lock);
        // bad PPA check
        spin_unlock(&line->lock);
    }
    ...
    return nvm_submit_io(dev, rqd);
}
```

This invokes the NVMe driver's `submit_io` callback:

```c
int nvm_submit_io(struct nvm_tgt_dev *tgt_dev, struct nvm_rq *rqd)
{
    ...
    ret = dev->ops->submit_io(dev, rqd);
    ...
}
```

Which is mapped to `nvme_nvm_submit_io`:

```c
static int nvme_nvm_submit_io(struct nvm_dev *dev, struct nvm_rq *rqd)
{
    ...
    blk_execute_rq_nowait(q, NULL, rq, 0, nvme_nvm_end_io);
}
```

### Block Layer Dispatch

`blk_execute_rq_nowait` inserts the request into the block I/O scheduler queue for **asynchronous execution**:

```c
void blk_execute_rq_nowait(struct request_queue *q,
                            struct gendisk *bd_disk,
                            struct request *rq, int at_head,
                            rq_end_io_fn *done)
{
    ...
    if (q->mq_ops) {
        blk_mq_sched_insert_request(rq, at_head, true, false, false);
        return;
    }
    spin_lock_irq(q->queue_lock);
    ...
    __elv_add_request(q, rq, where);
    __blk_run_queue(q);
    spin_unlock_irq(q->queue_lock);
}
```

Finally, `__blk_run_queue_uncond` invokes the registered `request_fn`. Note that **multiple threads may run this function concurrently**, which is why the active invocation count is tracked:

```c
inline void __blk_run_queue_uncond(struct request_queue *q)
{
    ...
    q->request_fn_active++;
    q->request_fn(q);
    q->request_fn_active--;
}
```

---

## 2026 Update Note

- This post was migrated from the original blog and language-polished in 2026.
- The code references are based on Linux kernel ~4.12–4.14. Modern kernels have since adopted `blk-mq` (multi-queue) and the legacy single-queue path shown here has been removed. The pblk subsystem itself has been superseded by NVMe ZNS.
