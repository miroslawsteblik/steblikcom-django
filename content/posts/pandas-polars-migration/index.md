---
title: "From Pandas to Polars: A Data Engineer's Migration Guide"
date: 2026-04-27
slug: pandas-polars-migration
summary: "A practical walkthrough of migrating production data pipelines from pandas to Polars — covering lazy frames, expressions, schema inference, encoding, and method-by-method translations."
tags:
  - polars
  - pandas
  - python
  - data-engineering
premium: false
draft: false
---

After a year of running pandas-based ETL on multi-GB parquet files, I finally bit the bullet and migrated everything to Polars. The result: pipelines that previously took 40+ minutes finishing in under 5, with a fraction of the memory footprint. Here's the practical translation guide I wish I'd had on day one.

## The Mental Shift: Expressions, Not Mutations

Pandas thinks in terms of mutating dataframes. Polars thinks in terms of _expressions_ — declarative recipes that describe what you want, which the query engine then optimizes.

```python
# pandas: imperative, eager
df["price_usd"] = df["price_eur"] * df["fx_rate"]
df = df[df["price_usd"] > 100]

# polars: declarative, composable
df = df.with_columns(
    (pl.col("price_eur") * pl.col("fx_rate")).alias("price_usd")
).filter(pl.col("price_usd") > 100)
```

This `pl.col(...)` expression is the unit of work in Polars. Once you internalize it, everything else clicks into place.

## Reading Data and Schema Inference

Polars infers schemas more aggressively than pandas, and it gets it right more often. But for production pipelines, never trust inference — declare schemas explicitly.

```python
import polars as pl

# Quick exploration: let Polars infer
df = pl.read_csv("trades.csv")

# Production: declare schema, sample more rows during inference
schema = {
    "trade_id": pl.Int64,
    "symbol": pl.Utf8,
    "price": pl.Float64,
    "quantity": pl.Int32,
    "executed_at": pl.Datetime,
}
df = pl.read_csv(
    "trades.csv",
    schema=schema,
    infer_schema_length=10_000,
)
```

For large files, `infer_schema_length` is critical — pandas' default of 100 rows often misclassifies columns when unusual types appear later in the file. Polars defaults to 100 too, but explicitly bumping it (or pinning `schema=`) eliminates the entire class of "type drift" bugs that surface only in production.

For Parquet, schemas come from file metadata — no inference needed. This alone is reason to standardize on Parquet for intermediate storage layers.

## Encoding: Strings, Categoricals, and Memory

This is where Polars genuinely shines for financial data. Repetitive string columns (tickers, exchanges, country codes) should be encoded as `Categorical` or, better, `Enum` when the value set is known and stable.

```python
# Stable, known set: use Enum (fastest, type-safe)
exchange_enum = pl.Enum(["NYSE", "NASDAQ", "LSE", "TSE"])
df = df.with_columns(pl.col("exchange").cast(exchange_enum))

# Unbounded but repetitive: use Categorical
df = df.with_columns(pl.col("symbol").cast(pl.Categorical))
```

On a 50M-row trades table I migrated, casting `symbol` and `exchange` to categoricals dropped memory from 8.2 GB to 1.4 GB. Pandas' `category` dtype offers the same in theory, but Polars' implementation is faster and far less buggy in group-by operations.

## Lazy Frames: The Real Win

If you take one thing from this article, take this: **use `LazyFrame` for any pipeline longer than two operations.**

A `LazyFrame` builds a query plan instead of executing immediately. Polars' optimizer then rewrites it — pushing filters down, pruning unused columns, combining projections, and parallelizing where possible.

```python
# Eager: each step materializes a full dataframe in memory
df = pl.read_parquet("trades.parquet")
df = df.filter(pl.col("executed_at") >= "2026-01-01")
df = df.with_columns((pl.col("price") * pl.col("quantity")).alias("notional"))
result = df.group_by("symbol").agg(pl.col("notional").sum())

# Lazy: nothing runs until .collect()
result = (
    pl.scan_parquet("trades.parquet")
    .filter(pl.col("executed_at") >= "2026-01-01")
    .with_columns((pl.col("price") * pl.col("quantity")).alias("notional"))
    .group_by("symbol")
    .agg(pl.col("notional").sum())
    .collect()
)
```

The lazy version reads only the columns it needs (`executed_at`, `price`, `quantity`, `symbol`), pushes the date filter down into the Parquet scan, and parallelizes the group-by. For a 200 GB partitioned dataset on my home lab box, this is the difference between OOMing and finishing in 90 seconds.

`scan_parquet`, `scan_csv`, and `scan_ndjson` are your lazy entry points. Use them by default.

## Method-by-Method Translation

Here's the cheat sheet I keep pinned during migrations:

| Pandas                       | Polars                                          |
| ---------------------------- | ----------------------------------------------- |
| `df.head(n)`                 | `df.head(n)`                                    |
| `df.shape[0]`                | `df.height`                                     |
| `df[df["x"] > 0]`            | `df.filter(pl.col("x") > 0)`                    |
| `df.assign(y=df["x"] * 2)`   | `df.with_columns((pl.col("x") * 2).alias("y"))` |
| `df.groupby("k")["v"].sum()` | `df.group_by("k").agg(pl.col("v").sum())`       |
| `df.merge(other, on="k")`    | `df.join(other, on="k")`                        |
| `df["x"].fillna(0)`          | `pl.col("x").fill_null(0)`                      |
| `df.sort_values("x")`        | `df.sort("x")`                                  |
| `pd.to_datetime(df["t"])`    | `pl.col("t").str.to_datetime()`                 |

Two gotchas worth remembering: Polars distinguishes `null` from `NaN` (pandas conflates them), and Polars uses `group_by` (snake_case) where pandas uses `groupby`.

## Intermediate: Conditionals and Window Functions

`when/then/otherwise` replaces pandas' `np.where` chains and `.apply()` calls:

```python
df = df.with_columns(
    pl.when(pl.col("notional") > 1_000_000)
      .then(pl.lit("large"))
      .when(pl.col("notional") > 100_000)
      .then(pl.lit("mid"))
      .otherwise(pl.lit("small"))
      .alias("trade_size")
)
```

Window functions use `.over()` and avoid the dreaded pandas `groupby().transform()` pattern:

```python
# Rolling average price per symbol — no groupby gymnastics
df = df.with_columns(
    pl.col("price")
      .rolling_mean(window_size=20)
      .over("symbol")
      .alias("ma_20")
)
```

## Advanced: Reusable Expressions

Because expressions are first-class objects, you can build a library of reusable transformations — something pandas makes painful:

```python
def normalize_ticker(col: str) -> pl.Expr:
    return (
        pl.col(col)
        .str.strip_chars()
        .str.to_uppercase()
        .str.replace_all(r"[^A-Z0-9.]", "")
        .alias(col)
    )

def notional(price: str = "price", qty: str = "quantity") -> pl.Expr:
    return (pl.col(price) * pl.col(qty)).alias("notional")

df = df.with_columns([normalize_ticker("symbol"), notional()])
```

This composes beautifully inside dbt-style transformation modules. I now keep a small `expressions.py` per project that gets imported across pipelines and unit-tested in isolation.

## Migration Tips

A few things I learned the hard way:

1. **Migrate read-then-write boundaries first.** Replace `pd.read_parquet` with `pl.scan_parquet` and convert back with `.to_pandas()` at the end of the pipeline. Then incrementally pull operations into the Polars side as you build confidence.
2. **Don't fight the immutability.** Polars frames are effectively immutable. Stop reaching for in-place updates and chained assignment — it's not coming back.
3. **Profile with `.explain()`.** On any lazy query, call `.explain()` to see the optimized plan. It's the equivalent of `EXPLAIN ANALYZE` for your dataframe code, and it'll teach you what the optimizer is actually doing.
4. **Watch the index.** Polars has no index. Anything that relied on pandas' `MultiIndex` needs to be rewritten with explicit columns. This is almost always an improvement.

The migration takes longer than you'd estimate — budget for the mental model shift, not just the API swap. But once your pipelines run in expressions and lazy plans, going back to pandas feels like writing assembly by hand.
