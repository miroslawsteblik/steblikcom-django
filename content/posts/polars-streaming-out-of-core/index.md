---
title: "Polars Streaming and Out-of-Core: When Your Data Won't Fit"
date: 2026-05-17
slug: polars-streaming-out-of-core
summary: "Practical guide to Polars' streaming engine — the 2025 rewrite, sinks, partitioned outputs, multiplexed pipelines, and how to process datasets that don't fit in RAM on a single node."
tags:
  - polars
  - streaming
  - out-of-core
  - parquet
  - performance
premium: false
draft: false
---

In the [last article](/posts/pandas-polars-migration) I covered the day-one mechanics of moving from pandas to Polars. This one tackles the question that comes about a week later: **how do you process a dataset that doesn't fit in RAM?**

For me that meant a 340 GB partitioned tick-data archive on a workstation with 64 GB of memory. Pandas couldn't even open one partition. Polars handles it, single-threaded, on a laptop. Here's how.

## The In-Memory Engine Has Limits

The default Polars engine — what you get from a plain `.collect()` — is heavily optimized but fundamentally in-memory. It assumes intermediate results fit in RAM, even if the source files don't.

For most workloads that's fine: column projection and predicate pushdown dramatically reduce what you actually load. But once intermediates exceed memory — wide joins, large group-bys, sorts — you'll OOM.

That's where the streaming engine comes in.

## The New Streaming Engine

Polars rewrote its streaming engine in 2025, replacing the original implementation with a new design based on Morsel-Driven Parallelism (the same architectural pattern HyPer and DuckDB use). As of 1.31+, the new engine is the one to reach for, and it'll eventually become the default.

Two things matter about it:

1. **Transparent fallback.** Operations that aren't yet implemented in streaming silently fall back to the in-memory engine for that part of the query. The legacy engine was much more brittle — you'd hit hard errors and have to rewrite.
2. **It's often faster.** Not just memory-friendlier — the new engine frequently beats the in-memory engine on PDS-H benchmarks, with the gap widening as data scales.

You opt in by passing `engine="streaming"` to `collect()`:

```python
import polars as pl

q = (
    pl.scan_parquet("trades/**/*.parquet")
    .filter(pl.col("executed_at") >= "2025-01-01")
    .group_by("symbol")
    .agg([
        (pl.col("price") * pl.col("quantity")).sum().alias("total_notional"),
        pl.col("price").mean().alias("avg_price"),
        pl.len().alias("trade_count"),
    ])
)

result = q.collect(engine="streaming")
```

This processes partitions in chunks ("morsels") rather than loading the full dataset. On my 340 GB archive, peak memory stayed under 8 GB.

> The older `collect(streaming=True)` API still works but routes through the legacy engine. Use `engine="streaming"` for new code.

## Sinks: When the Output Itself Is Huge

`collect()` materializes the result as a `DataFrame` — which means the **result** still needs to fit in memory, even with streaming. For pipelines that output gigabytes, use a `sink_*` method instead.

```python
# Streams both input and output — never materializes a full frame
(
    pl.scan_csv("raw_quotes/*.csv")
    .filter(pl.col("bid").is_not_null())
    .with_columns((pl.col("ask") - pl.col("bid")).alias("spread"))
    .sink_parquet("clean_quotes.parquet", compression="zstd")
)
```

Available sinks: `sink_parquet`, `sink_csv`, `sink_ipc`, `sink_ndjson`. Parquet with `zstd` is what I default to for intermediate storage — best compression-to-speed ratio for financial data I've measured.

A common pattern: **using a sink to convert CSV to Parquet at ingestion**. CSVs are lousy for analytics — slow to parse, no schema, no compression. Convert once at the boundary, then never read CSV again:

```python
from pathlib import Path

schema = {
    "trade_id": pl.Int64,
    "symbol": pl.Utf8,
    "price": pl.Float64,
    "quantity": pl.Int32,
    "executed_at": pl.Datetime,
}

(
    pl.scan_csv(
        Path("vendor_drop") / "*.csv",
        schema=schema,                 # always pin the schema at boundaries
        infer_schema_length=10_000,
    )
    .sink_parquet("staging/vendor.parquet", compression="zstd")
)
```

## Partitioned Sinks for Truly Large Output

For outputs that should be split across files — by row count, by key, or by both — pass a partitioning strategy to the sink:

```python
# Split output by symbol — one folder per ticker, hive-style layout
(
    pl.scan_parquet("trades_2025/*.parquet")
    .filter(pl.col("venue") == "NYSE")
    .sink_parquet(
        pl.PartitionByKey(
            "out/by_symbol/",
            by=["symbol"],
            include_key=False,
        ),
        compression="zstd",
        mkdir=True,
    )
)

# Cap files at 1M rows each
(
    pl.scan_parquet("huge.parquet")
    .sink_parquet(
        pl.PartitionMaxSize("out/chunked/", max_size=1_000_000),
        compression="zstd",
        mkdir=True,
    )
)

# Combined: partition by key AND limit file size
(
    pl.scan_parquet("trades_2025/*.parquet")
    .sink_parquet(
        pl.PartitionBy(
            "out/by_year/",
            key="year",
            max_rows_per_file=5_000_000,
            approximate_bytes_per_file=512 * 1024 * 1024,
        ),
        compression="zstd",
        mkdir=True,
    )
)
```

This is exactly the kind of operation where pandas plus a manual `for` loop has historically eaten an afternoon. Polars does it as part of the query plan, in parallel, with bounded memory.

## Multiplexed Sinks

You can stream the same query into multiple destinations simultaneously — useful when one intermediate feeds multiple downstream consumers (Parquet for the warehouse, IPC for an in-process consumer):

```python
lf = (
    pl.scan_parquet("raw/*.parquet")
    .filter(pl.col("status") == "filled")
    .with_columns((pl.col("price") * pl.col("quantity")).alias("notional"))
)

q1 = lf.sink_parquet("warehouse/filled.parquet", lazy=True)
q2 = lf.sink_ipc("cache/filled.arrow", lazy=True)

pl.collect_all([q1, q2])
```

The shared computation runs once, and results fan out to both files.

## What Doesn't Stream (Yet)

Honest disclosure: not every operation has a native streaming implementation. As of early 2026, the common ones that still fall back include:

- Some pivot operations
- Cumulative window functions over the entire frame (e.g. `cum_sum` without `.over()`)
- Certain non-equi joins
- A handful of complex `list.*` operations

When fallback happens, the streaming engine pipelines what it can, then hands off to the in-memory engine for the non-streaming portions. The query still runs — but if the non-streaming intermediate is huge, you'll still OOM.

Inspect what's actually happening with `.explain()` and `.show_graph()`:

```python
q = (
    pl.scan_parquet("...")
    .group_by("symbol")
    .agg(pl.col("notional").sum())
)

print(q.explain(engine="streaming"))

# Visual plan, colour-coded by memory pressure:
q.show_graph(engine="streaming", plan_stage="physical")
```

The graph view is invaluable when debugging "why is this still OOMing?" — non-streaming nodes stand out visually.

## Operational Patterns

What I run on my home lab (Ubuntu Server, 64 GB RAM, a fast NVMe scratch tier and slow spinning rust for cold storage):

1. **Ingest path is always sink-based.** Vendor CSV/JSON drops go through `scan_*` → `sink_parquet` with explicit schema and `zstd` compression. Memory stays bounded regardless of input size.
2. **Aggregations use `collect(engine="streaming")` by default.** I pin the engine explicitly so behaviour doesn't change when the default flips upstream.
3. **Inspect with `.explain()` before running anything that takes more than a minute.** Catches the fallback-to-in-memory traps early — far cheaper than an OOM at hour two.
4. **Watch for subtle bugs.** The new engine is mature but not perfect — there have been a couple of memory regressions on heavily-nested Parquet that were chased down across point releases. Pin your Polars version in production and validate upgrades on representative data before promoting.

## Beyond a Single Node

If your data outgrows a single machine, Polars Cloud extends the same lazy/streaming model to a distributed executor — same `LazyFrame` API, same expressions, just `.collect()` against a remote cluster. I haven't moved any of my own workloads there yet (single-node Polars handles everything I throw at it), but it's the natural escape hatch when you genuinely need distribution rather than just out-of-core.

For most data engineers maintaining medium-data pipelines, though, the headline is simpler: **a 64 GB box plus Polars streaming covers more workloads than most teams realize.** I've personally retired two Spark clusters this way — and the on-call pager is much quieter as a result.
