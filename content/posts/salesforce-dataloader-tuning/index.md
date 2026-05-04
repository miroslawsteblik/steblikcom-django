---
title: "Salesforce Data Loader: From v56 to v65 with Bulk API 2.0 — A 4× Speedup"
date: 2026-03-16
slug: salesforce-dataloader-tuning
summary: "How a few config.properties tweaks, a proper log4j2.properties, and a small PowerShell wrapper turned a slow nightly load into a fast async pipeline."
tags: [salesforce, dataloader, powershell, etl]
audience: "Data developers and Salesforce admins running Data Loader from the command line"
premium: true
draft: false
---

## TL;DR

I recently migrated our daily Salesforce load from **Data Loader v56** (Bulk API v1, SOAP-flavoured under the hood) to **v65** (Bulk API 2.0, REST + async) with about a **4× reduction in wall-clock time**.

Most of the gain comes from Bulk API 2.0's async server-side processing, but the tuning that actually made it production-ready was three smaller things:

1. A clean `config.properties` with `sfdc.useBulkV2Api=true` and explicit batch/timeout overrides.
2. Replacing the legacy `log-conf.xml` with a proper `log4j2.properties` and silencing noisy modules.
3. A PowerShell wrapper that calls `java -jar` directly so we can override paths and run multiple jobs from the same install.

This post is a copy-paste-friendly write-up of all three. If you're still on v56–v58, this is the migration path I'd recommend.

---

## Why v65 + Bulk API 2.0 actually matters

Quick refresher so the config decisions make sense:

- **Bulk API 1 (`sfdc.useBulkApi=true`)** splits your file into batches client-side, posts them, and you wait. Parallel-mode contention on shared parents is real, and serial mode serialises everything. Either way, your client is doing the orchestration.
- **Bulk API 2.0 (`sfdc.useBulkV2Api=true`)** uploads the whole job as one CSV stream, and **Salesforce decides how to chunk and parallelise it server-side**. You poll for completion. Your client does almost no work.

The official limits also moved up — Bulk API 2.0 supports up to 150M records per job vs 5M on Bulk v1 — but the bigger win for me was just removing the client-side batching loop. That's where the 4× came from. v65 ships with v2 as the recommended default and pairs it with a JRE 17 baseline and OAuth 2.0 Web Server Flow with PKCE, which is also a meaningful security upgrade over v56.

> **Heads up on the version jump**: v59+ already requires JRE 17, and v64+ swapped logging from log4j 1.x (`log-conf.xml`) to log4j 2.x (`log4j2.properties`). If you copied your old install's logging config across, it's silently doing nothing. That alone is worth the migration audit.

---

## 1. `config.properties` — the parts that matter

The default `config.properties` Salesforce ships is fine for the UI but suboptimal for headless batch use. Here's the trimmed, opinionated version I run in production. Everything not listed I leave at default.

```properties
# ---- API selection ----
# v1 OFF, v2 ON. Mutually exclusive — if both are true, v2 wins, but be explicit.
sfdc.useBulkApi=false
sfdc.useBulkV2Api=true

# ---- Auth ----
# OAuth Web Server Flow w/ PKCE is the default in v64+. For headless batch
# I still use encrypted password auth — simpler in CI, no browser hop.
sfdc.endpoint=https://login.salesforce.com
sfdc.username=integration.user@example.com.prod
sfdc.password=<encrypted-with-dataloader.key>
process.encryptionKeyFile=C:\\dataloader\\keys\\dataloader.key

# ---- Throughput ----
# v2 ignores client batch size for upload chunking, but loadBatchSize still
# governs the polling cadence and the row count per status check. 10k is a
# good middle ground; raising it past that mostly buys you log noise.
sfdc.loadBatchSize=10000

# Polling: v2 is async, so the client just waits. Don't set this too low or
# you'll spam the status endpoint.
sfdc.bulkApiCheckStatusInterval=5000

# ---- Network ----
sfdc.timeoutSecs=600
sfdc.connectionTimeoutSecs=60

# ---- Behaviour ----
sfdc.debugMessages=false
sfdc.debugMessagesFile=
process.outputError=C:\\dataloader\\logs\\error.csv
process.outputSuccess=C:\\dataloader\\logs\\success.csv
process.statusOutputDirectory=C:\\dataloader\\logs

# ---- Date handling ----
# Force ISO-8601 with timezone. Saves you from the Excel-ate-my-dates problem.
process.useEuropeanDates=false
sfdc.timezone=UTC
```

A few notes from migration scars:

- **`sfdc.useBulkApi` and `sfdc.useBulkV2Api` are not the same key.** I've seen people set the v1 flag to true and assume "Bulk = Bulk." It's not. Set v1 to `false` explicitly so future-you doesn't flip the wrong one.
- **`sfdc.loadBatchSize` semantics changed.** Under v1 it was the size of each PATCH the client sent. Under v2 it's much more about polling/reporting granularity, since the server chunks the upload itself. Don't optimise it the way you used to — bigger isn't automatically better.
- **`process.statusOutputDirectory` is per-process, not global.** If you run multiple jobs from one install, point each one at a separate directory or you'll race on `success.csv` / `error.csv`.

---

## 2. Replace `log-conf.xml` with `log4j2.properties`

This is the one that bit me hardest. v64+ uses log4j 2.x, and the old `log-conf.xml` from your v56 install is **silently ignored** — Data Loader falls back to its built-in defaults, which log a frankly ridiculous amount on INFO. On a 0.5M-record load that's gigabytes of mostly-useless transport chatter.

Drop a `log4j2.properties` next to your `config.properties`:

```properties
# log4j2.properties — Data Loader v64+
status = warn
name = DataLoaderConfig

# ---- Appenders ----
appender.console.type = Console
appender.console.name = STDOUT
appender.console.target = SYSTEM_OUT
appender.console.layout.type = PatternLayout
appender.console.layout.pattern = %d{yyyy-MM-dd HH:mm:ss} %-5p %c{1} - %m%n

appender.file.type = RollingFile
appender.file.name = FILE
appender.file.fileName = C:/dataloader/logs/dataloader.log
appender.file.filePattern = C:/dataloader/logs/dataloader-%d{yyyy-MM-dd}-%i.log.gz
appender.file.layout.type = PatternLayout
appender.file.layout.pattern = %d{ISO8601} %-5p [%t] %c - %m%n
appender.file.policies.type = Policies
appender.file.policies.size.type = SizeBasedTriggeringPolicy
appender.file.policies.size.size = 25MB
appender.file.policies.time.type = TimeBasedTriggeringPolicy
appender.file.strategy.type = DefaultRolloverStrategy
appender.file.strategy.max = 14

# ---- Root: WARN is the right default for prod batch ----
rootLogger.level = warn
rootLogger.appenderRef.console.ref = STDOUT
rootLogger.appenderRef.file.ref = FILE

# ---- Data Loader's own loggers: keep INFO so you still see job progress ----
logger.dataloader.name = com.salesforce.dataloader
logger.dataloader.level = info

# ---- Silence the noisy modules ----
# HTTP wire dumps — every request body and header. Massive, useless 99% of the time.
logger.httpwire.name = org.apache.http.wire
logger.httpwire.level = error
logger.httpheaders.name = org.apache.http.headers
logger.httpheaders.level = error
logger.httpclient.name = org.apache.http
logger.httpclient.level = warn

# Salesforce SOAP/CXF stack — chatty on auth and metadata refresh
logger.sforce.name = com.sforce
logger.sforce.level = warn

# Spring (Data Loader uses it for process-conf.xml). Boots noisily.
logger.spring.name = org.springframework
logger.spring.level = error

# Eclipse SWT/Jetty (only relevant if UI is launched, but harmless in batch)
logger.eclipse.name = org.eclipse
logger.eclipse.level = error

# Hibernate validator + jackson — show up during config parse
logger.hibernate.name = org.hibernate
logger.hibernate.level = error
logger.jackson.name = com.fasterxml.jackson
logger.jackson.level = warn
```

Two things this gets you that the default doesn't:

1. **Log volume drops by ~95%** on a typical run. On the same 0.5M-record job, my log went from ~0.4 GB to ~4 MB. That's not a perf win in itself, but it stops disk I/O from being a bottleneck on slower volumes — and it makes the logs actually grep-able when something does go wrong.
2. **Rolling file with size + time triggers**, gzipped, 14-day retention. The default appender is a single ever-growing file, which is fine until your nightly job fills the disk on a long weekend.

When you're debugging a real problem, temporarily flip `logger.dataloader.level` to `debug` and `logger.httpwire.level` to `debug` for one run. Don't leave them on.

---

## 3. PowerShell wrapper — call `java -jar` directly

The shipped `dataloader.bat` / `dataloader_console.bat` is a black box that hard-codes paths inside the install directory. That's fine for one job. The moment you have multiple processes, multiple environments (sandbox vs prod), or want to run from a scheduled task with explicit logging, you want to call the JAR yourself.

The documented invocation is:

```
java -jar dataloader-<x.y.z>.jar salesforce.config.dir=<dir with config.properties + process-conf.xml> process.name=<process> run.mode=batch
```

Anything you put on the command line **overrides** the same key in `config.properties`. That's the lever we want.

Here's the wrapper I use. It picks up the right Data Loader install, lets you point at any config dir, and forwards arbitrary key=value overrides:

```powershell
# Invoke-DataLoader.ps1
# Wrapper around Salesforce Data Loader v65 to run a named process in batch mode
# with explicit config and overridable settings. Tested on PowerShell 7+.

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $ConfigDir,                 # folder containing config.properties + process-conf.xml + log4j2.properties

    [Parameter(Mandatory)]
    [string] $ProcessName,               # bean id from process-conf.xml

    [string] $DataLoaderHome = 'C:\Program Files\salesforce.com\Data Loader',
    [string] $JavaHome      = $env:JAVA_HOME,
    [string] $LogConfigFile,             # optional: explicit path to log4j2.properties

    [hashtable] $Overrides = @{}         # extra key=value pairs, e.g. @{ 'sfdc.endpoint' = '...' }
)

$ErrorActionPreference = 'Stop'

# --- Resolve the JAR (filename includes version, so glob it) ---
$jar = Get-ChildItem -Path (Join-Path $DataLoaderHome 'dataloader-*.jar') |
       Sort-Object Name -Descending |
       Select-Object -First 1

if (-not $jar) {
    throw "No dataloader-*.jar found under $DataLoaderHome"
}

# --- Resolve java ---
$java = if ($JavaHome) { Join-Path $JavaHome 'bin\java.exe' } else { 'java' }
if ($JavaHome -and -not (Test-Path $java)) {
    throw "java.exe not found at $java"
}

# --- Validate config dir ---
if (-not (Test-Path (Join-Path $ConfigDir 'config.properties'))) {
    throw "config.properties not found in $ConfigDir"
}
if (-not (Test-Path (Join-Path $ConfigDir 'process-conf.xml'))) {
    throw "process-conf.xml not found in $ConfigDir"
}

# --- Build the JVM args ---
$jvmArgs = @(
    '-Xms512m',
    '-Xmx2g',
    '-Dfile.encoding=UTF-8'
)

# Point log4j2 at the config file in our config dir (or an explicit path)
if (-not $LogConfigFile) {
    $LogConfigFile = Join-Path $ConfigDir 'log4j2.properties'
}
if (Test-Path $LogConfigFile) {
    $jvmArgs += "-Dlog4j2.configurationFile=$LogConfigFile"
} else {
    Write-Warning "log4j2.properties not found at $LogConfigFile — Data Loader will fall back to defaults (very noisy)."
}

# --- Build the Data Loader args ---
$dlArgs = @(
    "salesforce.config.dir=$ConfigDir",
    "process.name=$ProcessName",
    'run.mode=batch'
)

# Forward overrides as key=value
foreach ($k in $Overrides.Keys) {
    $dlArgs += "$k=$($Overrides[$k])"
}

# --- Run ---
Write-Host "[$(Get-Date -Format s)] Starting Data Loader: $ProcessName" -ForegroundColor Cyan
Write-Host "  jar:        $($jar.Name)"
Write-Host "  configDir:  $ConfigDir"
Write-Host "  log4j2:     $LogConfigFile"
if ($Overrides.Count -gt 0) {
    Write-Host "  overrides:  $($Overrides.Keys -join ', ')"
}

& $java @jvmArgs '-jar' $jar.FullName @dlArgs
$code = $LASTEXITCODE

Write-Host "[$(Get-Date -Format s)] Data Loader exited with code $code" -ForegroundColor Cyan
exit $code
```

Usage from a scheduler or another script:

```powershell
# Daily Account upsert into prod
.\Invoke-DataLoader.ps1 `
    -ConfigDir   'C:\dataloader\jobs\account-upsert-prod' `
    -ProcessName 'csvUpsertAccount' `
    -Overrides   @{
        'sfdc.endpoint'      = 'https://login.salesforce.com'
        'sfdc.loadBatchSize' = '10000'
        'dataAccess.name'    = 'C:\dataloader\inbox\accounts_2026-04-27.csv'
    }
```

A few things this pattern unlocks:

- **One install, many jobs.** Each job lives in its own folder under `C:\dataloader\jobs\<job>` with its own `config.properties`, `process-conf.xml`, and `log4j2.properties`. No more editing the install dir for every change.
- **Sandbox vs prod is a CLI flag**, not two installs. Override `sfdc.endpoint` and `sfdc.username` from the wrapper.
- **Log rotation behaves**, because we explicitly point log4j at our properties file via `-Dlog4j2.configurationFile`. Without that flag, log4j 2 will look for `log4j2.properties` on the classpath, find Data Loader's bundled default, and use it. That's the silent-fallback bug from §2.
- **Exit code propagation.** The wrapper exits with `$LASTEXITCODE` from java, so a Task Scheduler / GitHub Actions / cron-on-WSL caller actually knows the job failed.

---

## What actually drove the 4× speedup (in order of impact)

For our workload — daily refresh, ~0.M record upsert into a custom object with two lookups — the breakdown was roughly:

1. **Bulk API 2.0 async processing** (~3× on its own). Server-side chunking + parallelism + no client-side batch loop. This is the headline.
2. **Killing log noise** (~1.2×). Less disk I/O, less stdout pressure when running over a logged-in RDP session, and a smaller log to ship to our log aggregator.
3. **JRE 17** (small but real). v65 requires it, and the G1GC defaults handle Data Loader's allocation pattern noticeably better than the JRE 8 defaults v56 ran on.

Those compose to roughly the 4× I measured end-to-end. Your mileage will vary — if your bottleneck is API limits, picklist validation, triggers, or a particularly trigger-happy duplicate rule, none of the above will save you. Bulk 2.0 helps the *transport*; it doesn't help bad org config.

---

## Gotchas I'd flag

- **Hard delete in Bulk 2.0** behaves the same as v1 (immediate, no Recycle Bin). Don't assume the migration changed anything about that — it didn't.
- **External ID upserts**: confirm `sfdc.externalIdField` is set in `process-conf.xml`, not just `config.properties`. v2 is stricter about validating this at job submission rather than during upload.
- **OAuth Web Server Flow with PKCE** is great for interactive use but a pain for headless. For batch I stayed on encrypted-password auth — it's still supported and explicitly called out as unaffected by the OAuth flow changes in v64+.
- **`log4j2.configurationFile` must be a real path, not a classpath URI**, when you pass it via `-D`. If the file doesn't exist log4j silently falls back. Always check the first few lines of your log file after a deploy — they should match your pattern, not the default.

---

## Closing

The migration itself was about half a day of work, mostly spent on the logging config and writing the wrapper. The org-side change was literally one checkbox (`sfdc.useBulkV2Api`). If you're still on a pre-v64 Data Loader, the JRE-17 + log4j2 transition is the only real lift, and it's worth it — both for the speed and for not running an unmaintained logging stack against a production integration user.

Source files in this post — `config.properties`, `log4j2.properties`, `Invoke-DataLoader.ps1` — are meant to be dropped in and edited. The Salesforce-published reference for the keys themselves is the *Data Loader Process Configuration Parameters* page in the official docs, which is the canonical list when you're trying to remember whether it's `sfdc.timeoutSecs` or `sfdc.connectionTimeoutSecs` (it's both, and they mean different things).
