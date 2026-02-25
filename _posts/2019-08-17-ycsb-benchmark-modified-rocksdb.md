---
title: "Running YCSB Benchmarks on a Modified RocksDB Build"
date: 2019-08-17 10:00:00 +0900
categories: [Research, Database]
tags: [rocksdb, ycsb, benchmark, jni, open-channel-ssd, liblightnvm]
image:
  path: /assets/img/posts/research/ycsbrocksdb1.png
description: "Step-by-step guide to benchmarking a custom-modified RocksDB with YCSB — building a JNI package from source-modified RocksDB and integrating it into the YCSB framework."
---

## Background

If you want to benchmark the **stock version** of RocksDB with YCSB, simply follow the official [YCSB RocksDB README](https://github.com/brianfrankcooper/YCSB/blob/master/rocksdb/README.md). Maven will download the RocksDB package automatically.

However, if you have **modified the RocksDB source code** and want to evaluate your custom version's performance, you need to:

1. Build RocksDB as a **Java JNI package**.
2. Replace YCSB's default RocksDB JNI package with yours.

In my case, I modified RocksDB's storage backend to use [liblightnvm](https://github.com/OpenChannelSSD/liblightnvm) instead of POSIX I/O, enabling Open-Channel SSD as the storage target. Beyond the steps described below, I also had to implement a few custom JNI functions. For typical algorithmic or code-level modifications, the instructions in this post should be sufficient.

## Step 1: Build the RocksDB JNI Package

First, ensure your modified RocksDB source code compiles and works correctly:

```bash
make release
# Verify that db_bench runs without errors
```

Once confirmed, you need to **Java-compile** RocksDB. The `java/` directory in the RocksDB source tree contains everything related to the JNI package.

### Simplify Compression Dependencies

RocksDB supports five compression methods, but you probably do not need all of them. To save build time, comment out the unused ones in the `Makefile`. For example, to keep only **Snappy** compression:

```makefile
# A version of each $(LIBOBJECTS) compiled with -fPIC
java_static_libobjects = $(patsubst %,jls/%,$(LIBOBJECTS))
CLEAN_FILES += jls

ifneq ($(ROCKSDB_JAVA_NO_COMPRESSION), 1)
# JAVA_COMPRESSIONS = libz.a libbz2.a libsnappy.a liblz4.a libzstd.a
JAVA_COMPRESSIONS = libsnappy.a
endif

# JAVA_STATIC_FLAGS = -DZLIB -DBZIP2 -DSNAPPY -DLZ4 -DZSTD
JAVA_STATIC_FLAGS = -DSNAPPY
# JAVA_STATIC_INCLUDES = -I./zlib-... -I./bzip2-... -I./snappy-... -I./lz4-.../lib -I./zstd-.../lib
JAVA_STATIC_INCLUDES = -I./snappy-$(SNAPPY_VER)
```

### Disable Cross-Platform Build

Since you only need a native build, modify the `rocksdbjavastaticrelease` rule to skip Vagrant-based cross-compilation:

```makefile
rocksdbjavastaticrelease: rocksdbjavastatic
  # cd java/crossbuild && vagrant destroy -f && vagrant up linux32 && ...
  cd java;jar -cf target/$(ROCKSDB_JAR_ALL) HISTORY*.md
  # cd java/target;jar -uf $(ROCKSDB_JAR_ALL) librocksdbjni-*.so librocksdbjni-*.jnilib
  cd java/target;jar -uf $(ROCKSDB_JAR_ALL) librocksdbjni-*.so
  cd java/target/classes;jar -uf ../$(ROCKSDB_JAR_ALL) org/rocksdb/*.class org/rocksdb/util/*.class
```

### Build

```bash
make rocksdbjavastaticrelease -j16
```

On success, you will find the JNI package at:

```
rocksdb/java/target/rocksdbjni-5.18.3.jar
```

> The version number (e.g., `5.18.3`) will vary depending on your RocksDB source.

## Step 2: Compile YCSB with RocksDB Binding

### Clone and Configure YCSB

```bash
git clone https://github.com/brianfrankcooper/YCSB.git
cd YCSB
git checkout 0.15.0
```

Add the following dependencies to `YCSB/core/pom.xml` inside the `<dependencies>` section:

```xml
<dependency>
    <groupId>org.apache.htrace</groupId>
    <artifactId>htrace-core4</artifactId>
    <version>4.1.0-incubating</version>
</dependency>
<dependency>
    <groupId>org.hdrhistogram</groupId>
    <artifactId>HdrHistogram</artifactId>
    <version>2.1.4</version>
</dependency>
```

### Build the RocksDB Binding Only

Running `mvn clean package` without filters would download dependencies for **all** database bindings (HBase, MongoDB, etc.), which takes a very long time. Build only the RocksDB binding:

```bash
mvn -pl com.yahoo.ycsb:rocksdb-binding -am clean package
```

Verify that `htrace-core4-4.1.0-incubating.jar` and `HdrHistogram-2.1.4.jar` appear in `YCSB/rocksdb/target/dependency/`.

## Step 3: Replace the Default JNI Package

By default, YCSB downloads a specific RocksDB version (e.g., `5.11.3` as specified in `YCSB/pom.xml`). To use **your** custom build:

1. **Copy** your JNI package into YCSB's dependency directory:

   ```bash
   cp rocksdb/java/target/rocksdbjni-5.18.3.jar YCSB/rocksdb/target/dependency/
   ```

2. **Delete** the default version:

   ```bash
   rm YCSB/rocksdb/target/dependency/rocksdbjni-5.11.3.jar
   ```

## Step 4: Run YCSB

### Load Data

```bash
bin/ycsb.sh load rocksdb -s -P workloads/workloada \
  -p rocksdb.dir=/home/rocky/ycsbdata
```

Check the LOG file header to confirm your custom RocksDB version is active.

### Run a Workload

```bash
bin/ycsb.sh run rocksdb -s -P workloads/workloada \
  -p rocksdb.dir=/home/rocky/ycsbdata
```

## Tuning Parameters

### YCSB Workload Parameters

The default `fieldcount` and `fieldlength` values are small, so experiments finish very quickly. Edit the workload files in `YCSB/workloads/` to use realistic sizes.

### RocksDB Options

RocksDB configuration is managed in:

```
YCSB/rocksdb/src/main/java/com/yahoo/ycsb/db/rocksdb/RocksDBClient.java
```

Look at the `initRocksDB()` function, where options like compaction style, parallelism, and log level are set:

```java
if (cfDescriptors.isEmpty()) {
    final Options options = new Options()
        .optimizeLevelStyleCompaction()
        .setCreateIfMissing(true)
        .setCreateMissingColumnFamilies(true)
        .setIncreaseParallelism(rocksThreads)
        .setMaxBackgroundCompactions(rocksThreads)
        .setInfoLogLevel(InfoLogLevel.INFO_LEVEL);
    dbOptions = options;
    return RocksDB.open(options, rocksDbDir.toAbsolutePath().toString());
}
```

Refer to `java/src/main/java/org/rocksdb/Options.java` and `DBOptions.java` in the RocksDB source for available setters.

If you modify `RocksDBClient.java`, rebuild the binding (without `clean` to save time):

```bash
mvn -pl com.yahoo.ycsb:rocksdb-binding -am package
```

Then delete the regenerated default JAR again and re-run your benchmarks.

---

## 2026 Update Note

- This post was migrated from the original blog and language-polished in 2026.
- For modern YCSB + RocksDB benchmarking, newer YCSB versions and RocksDB's updated Java API may differ slightly. The overall workflow — build JNI, replace the default JAR, configure options — remains the same.
