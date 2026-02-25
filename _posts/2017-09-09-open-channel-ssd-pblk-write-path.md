---
title: "Open-Channel SSD Series (5): pblk Write Path — Kernel Code Analysis"
date: 2017-09-09 11:00:00 +0900
categories: [Research, Open-Channel SSD]
tags: [open-channel-ssd, lightnvm, pblk, linux-kernel, kernel-code, write-path]
description: "Kernel source code walkthrough of the pblk write path in the LightNVM Open-Channel SSD subsystem — from write-buffer insertion through ring buffer to NVMe dispatch."
---

> Related paper: Bjørling et al., "LightNVM: The Linux Open-Channel SSD Subsystem," *FAST'17*.

## Write Thread Initialization

During pblk initialization, a dedicated **writer kernel thread** is created:

```c
/* physical block device target */
static struct nvm_tgt_type tt_pblk = {
    .name     = "pblk",
    .version  = {1, 0, 0},
    .make_rq  = pblk_make_rq,
    .capacity = pblk_capacity,
    .init     = pblk_init,
    .exit     = pblk_exit,
    .sysfs_init = pblk_sysfs_init,
    .sysfs_exit = pblk_sysfs_exit,
};
```

`pblk_init` calls `pblk_writer_init`, which sets up a timer and creates the writer thread:

```c
static int pblk_writer_init(struct pblk *pblk)
{
    setup_timer(&pblk->wtimer, pblk_write_timer_fn,
                (unsigned long)pblk);
    mod_timer(&pblk->wtimer, jiffies + msecs_to_jiffies(100));

    pblk->writer_ts = kthread_create(pblk_write_ts, pblk,
                                      "pblk-writer-t");
    if (IS_ERR(pblk->writer_ts)) {
        pr_err("pblk: could not allocate writer kthread\n");
        return PTR_ERR(pblk->writer_ts);
    }

    return 0;
}
```

The writer thread runs `pblk_write_ts`, which loops calling `pblk_submit_write` and yields to the I/O scheduler when there is no work:

```c
int pblk_write_ts(void *data)
{
    struct pblk *pblk = data;

    while (!kthread_should_stop()) {
        if (!pblk_submit_write(pblk))
            continue;
        set_current_state(TASK_INTERRUPTIBLE);
        io_schedule();
    }

    return 0;
}
```

## Write Path

### Entry Point

Writes from the file system enter through `pblk_make_rq`, the same entry point as reads:

```c
static blk_qc_t pblk_make_rq(struct request_queue *q, struct bio *bio)
{
    struct pblk *pblk = q->queuedata;

    if (bio_op(bio) == REQ_OP_DISCARD) {
        pblk_discard(pblk, bio);
        if (!(bio->bi_opf & REQ_PREFLUSH)) {
            bio_endio(bio);
            return BLK_QC_T_NONE;
        }
    }

    switch (pblk_rw_io(q, pblk, bio)) {
    case NVM_IO_ERR:
        bio_io_error(bio);
        break;
    case NVM_IO_DONE:
        bio_endio(bio);
        break;
    }

    return BLK_QC_T_NONE;
}
```

---

### Read / Write Dispatch

`pblk_rw_io` separates read and write paths. Reads go through `pblk_submit_read`; writes go through `pblk_write_to_cache`:

```c
static int pblk_rw_io(struct request_queue *q, struct pblk *pblk,
                       struct bio *bio)
{
    if (bio_data_dir(bio) == READ) {
        ret = pblk_submit_read(pblk, bio);
        ...
        return ret;
    }

    // Write path
    return pblk_write_to_cache(pblk, bio, PBLK_IOTYPE_USER);
}
```

---

### pblk_write_to_cache — Inserting Data into the Ring Buffer

This function copies data from the bio into pblk's **write ring buffer** and saves the write context. Typically, 4 KB data chunks from the bio are copied to the ring buffer:

```c
int pblk_write_to_cache(struct pblk *pblk, struct bio *bio,
                          unsigned long flags)
{
    struct pblk_w_ctx w_ctx;
    sector_t lba = pblk_get_lba(bio);
    unsigned int bpos, pos;
    int nr_entries = pblk_get_secs(bio);
    int i, ret;

retry:
    ret = pblk_rb_may_write_user(&pblk->rwb, bio,
                                  nr_entries, &bpos);
    switch (ret) {
    case NVM_IO_REQUEUE:
        io_schedule();
        goto retry;
    case NVM_IO_ERR:
        pblk_pipeline_stop(pblk);
        goto out;
    }

    pblk_ppa_set_empty(&w_ctx.ppa);
    w_ctx.flags = flags;
    if (bio->bi_opf & REQ_PREFLUSH)
        w_ctx.flags |= PBLK_FLUSH_ENTRY;

    for (i = 0; i < nr_entries; i++) {
        void *data = bio_data(bio);
        w_ctx.lba = lba + i;
        pos = pblk_rb_wrap_pos(&pblk->rwb, bpos + i);
        pblk_rb_write_entry_user(&pblk->rwb, data, w_ctx, pos);
        bio_advance(bio, PBLK_EXPOSED_PAGE_SIZE);
    }

    pblk_rl_inserted(&pblk->rl, nr_entries);

out:
    pblk_write_should_kick(pblk);
    return ret;
}
```

Key helper functions:

- **`pblk_rb_may_write_user`** — atomically verifies (i) enough space exists in the write buffer, and (ii) the current I/O type has sufficient budget per the rate limiter.
- **`pblk_rb_write_entry_user`** — copies the data into the ring buffer and updates the **L2P mapping table** via the call chain: `pblk_rb_write_entry_user` → `pblk_update_map_cache` → `pblk_update_map` → `pblk_trans_map_set`.

### L2P Mapping Update

When data enters the write buffer, the mapping table must be updated (the new cache address replaces any previous mapping):

```c
void pblk_update_map(struct pblk *pblk, sector_t lba,
                      struct ppa_addr ppa)
{
    struct ppa_addr ppa_l2p;

    if (!(lba < pblk->rl.nr_secs)) {
        WARN(1, "pblk: corrupted L2P map request\n");
        return;
    }

    spin_lock(&pblk->trans_lock);
    ppa_l2p = pblk_trans_map_get(pblk, lba);

    if (!pblk_addr_in_cache(ppa_l2p) && !pblk_ppa_empty(ppa_l2p))
        pblk_map_invalidate(pblk, ppa_l2p);

    pblk_trans_map_set(pblk, lba, ppa);
    spin_unlock(&pblk->trans_lock);
}
```

```c
static inline void pblk_trans_map_set(struct pblk *pblk,
                                       sector_t lba,
                                       struct ppa_addr ppa)
{
    if (pblk->ppaf_bitsize < 32) {
        u32 *map = (u32 *)pblk->trans_map;
        map[lba] = pblk_ppa64_to_ppa32(pblk, ppa);
    } else {
        u64 *map = (u64 *)pblk->trans_map;
        map[lba] = ppa.ppa;
    }
}
```

---

### Kicking the Writer Thread

After inserting data into the ring buffer, `pblk_write_should_kick` checks whether enough sectors are available to form a complete write and wakes the writer thread:

```c
void pblk_write_should_kick(struct pblk *pblk)
{
    unsigned int secs_avail = pblk_rb_read_count(&pblk->rwb);

    if (secs_avail >= pblk->min_write_pgs)
        pblk_write_kick(pblk);
}
```

```c
static void pblk_write_kick(struct pblk *pblk)
{
    wake_up_process(pblk->writer_ts);
    mod_timer(&pblk->wtimer, jiffies + msecs_to_jiffies(1000));
}
```

`wake_up_process` (from `kernel/sched/core.c`) moves the writer thread back to the runnable set, which causes `pblk_submit_write` to execute.

---

### pblk_submit_write — Flushing the Buffer to Media

The writer thread reads entries from the ring buffer, forms a bio, and submits the I/O:

```c
static int pblk_submit_write(struct pblk *pblk)
{
    ...
    // Read available entries from ring buffer into a bio
    pblk_rb_read_to_bio(&pblk->rwb, rqd, bio, pos,
                         secs_to_sync, secs_avail);
    ...
    // Submit the I/O
    pblk_submit_io_set(pblk, rqd);
}
```

**`pblk_rb_read_to_bio`** reads entries from the ring buffer and adds them to the bio. To avoid an extra memory copy, a **page reference** to the write buffer is used directly.

---

### pblk_submit_io_set — Write Request Setup

This function performs the final address mapping (logical → physical) and submits the request:

```c
static int pblk_submit_io_set(struct pblk *pblk, struct nvm_rq *rqd)
{
    ...
    /* Assign LBAs to PPAs and build the request structure */
    err = pblk_setup_w_rq(pblk, rqd, c_ctx, &erase_ppa);
    ...
    /* Submit metadata write for the previous data line */
    err = pblk_sched_meta_io(pblk, rqd->ppa_list, rqd->nr_ppas);
    /* Submit data write */
    err = pblk_submit_io(pblk, rqd);
}
```

```c
static int pblk_setup_w_rq(struct pblk *pblk, struct nvm_rq *rqd,
                             struct pblk_c_ctx *c_ctx,
                             struct ppa_addr *erase_ppa)
{
    ...
    ret = pblk_alloc_w_rq(pblk, rqd, nr_secs, pblk_end_io_write);
    ...
    if (likely(!e_line || !atomic_read(&e_line->left_eblks)))
        pblk_map_rq(pblk, rqd, c_ctx->sentry,
                     lun_bitmap, valid, 0);
    else
        pblk_map_erase_rq(pblk, rqd, c_ctx->sentry,
                           lun_bitmap, valid, erase_ppa);
    ...
}
```

- **`pblk_alloc_w_rq`** — allocates and initializes the `nvm_rq` structure.
- **`pblk_map_rq` / `pblk_map_erase_rq`** — assign physical addresses to each sector. These functions are safe to call without locks because the write buffer's sync backpointer guarantees that only the single writer thread accesses a particular entry at any given time.

---

### NVMe Dispatch

From here, the path through the NVMe stack is identical to the read path:

```
pblk_submit_io → nvm_submit_io → nvme_nvm_submit_io
  → blk_execute_rq_nowait → __blk_run_queue → request_fn
```

The request is inserted into the block I/O scheduler for asynchronous execution. Multiple threads may invoke `request_fn` concurrently, so the block layer tracks the active invocation count accordingly.

---

## 2026 Update Note

- This post was migrated from the original blog and language-polished in 2026.
- The code references are based on Linux kernel ~4.12–4.14. The pblk write path, ring buffer design, and the legacy single-queue block layer have all been superseded in modern kernels (blk-mq, NVMe ZNS).
