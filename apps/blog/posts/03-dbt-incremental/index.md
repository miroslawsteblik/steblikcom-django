---
title: "Incremental dbt models without losing your mind"
slug: 03-dbt-incremental
date: 2026-02-12
tags: [dbt, data-engineering]
draft: false
summary: A few patterns for incremental models that survive backfills.
---

Body in markdown here. Code blocks render with Pygments.

​```python
import polars as pl
df = pl.read_parquet("trades.parquet")
​```
