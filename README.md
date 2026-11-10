# Overview

Gova is your AI powered community moderator, keepign your community cleanin real time.

## Performance


| Scope                                | Messages | Total chars | Mean chars | Median | Min | Max | Mean words |
| ------------------------------------ | -------: | ----------: | ---------: | -----: | --: | --: | ---------: |
| Full corpus                          |      360 |       5,714 |      15.87 |     15 |   2 |  62 |       3.06 |
| Day 1                                |      120 |       2,058 |      17.15 |      - |   2 |  62 |          - |
| Day 2                                |      120 |       1,907 |      15.89 |      - |   3 |  38 |          - |
| Day 3                                |      120 |       1,749 |      14.57 |      - |   3 |  32 |          - |
| Latency sample (even, 60)            |       60 |         919 |      15.32 |     15 |   2 |  37 |       3.07 |
| Throughput sample (first 20/day, 60) |       60 |       1,193 |      19.88 |     20 |   4 |  40 |       3.87 |

The real-LLM run below used the 60-message samples, not the full corpus.

### Flags

| Flag                              | Default                      | Effect                                                                                                                                                                                                       |
| --------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `GOVA_PERF_TESTS`                 | unset                        | Master switch. Without it every `perf`-marked test is skipped.                                                                                                                                               |
| `GOVA_PERF_REAL_LLM`              | unset                        | Calls the configured provider instead of the stub. Also stops the dummy LLM credentials from being injected, so `.env` is used.                                                                              |
| `GOVA_PERF_REAL_LLM_MAX_MESSAGES` | `60`                         | Caps the real-LLM latency sample and the throughput offered load (`cap / 3` messages per day) to bound API cost and runtime. Ignored when the LLM is stubbed.                                                |
| `GOVA_PERF_THROUGHPUT_RATES`      | `1,5,10`                     | Comma-separated offered rates in messages per minute; one parametrized test per rate. Each rate offers `rate * 120` messages per day (capped in real-LLM mode).                                              |
| `GOVA_PERF_CONCURRENCY`           | `8`                          | Semaphore bounding in-flight `on_message` calls in the throughput test. Raises/lowers achievable rate via Little's Law (`throughput ~= concurrency / latency`). Does not affect the sequential latency test. |
| `GOVA_PERF_MODEL_LATENCY_MS`      | `5`                          | Simulated per-call model latency in stub mode. Ignored when `GOVA_PERF_REAL_LLM` is set.                                                                                                                     |
| `GOVA_PERF_LATENCY_BUDGET_MS`     | `250` (stub) / `1000` (real) | Pass/fail ceiling for p99 latency in the latency test.                                                                                                                                                       |

### Results

Measured on Python 3.13.7 / pytest 9.2.0 with the real LLM, 60 messages,
concurrency 8. Latency sample: mean 15.32 chars/message; throughput sample:
mean 19.88 chars/message.

| Mode     | Messages |      Mean |       p50 |       p90 |       p95 |       p99 |
| -------- | -------: | --------: | --------: | --------: | --------: | --------: |
| real-llm |       60 | 244.52 ms | 231.52 ms | 254.30 ms | 414.16 ms | 544.50 ms |

| Offered rate | Offered | Completed | Elapsed |       Achieved | Concurrency |
| -----------: | ------: | --------: | ------: | -------------: | ----------: |
|    1 msg/min |      60 |        60 | 3.250 s | 1107.8 msg/min |           8 |
|    5 msg/min |      60 |        60 | 2.280 s | 1579.2 msg/min |           8 |
|   10 msg/min |      60 |        60 | 2.288 s | 1573.2 msg/min |           8 |

Achievable throughput is bounded by Little's Law: `concurrency / per-message
latency`. At ~245 ms mean latency and concurrency 8 the pipeline sustains
roughly 1.1k-1.6k messages per minute in this run.

### Tuning

- Raise `GOVA_PERF_THROUGHPUT_RATES` to test heavier offered loads; in real-LLM
  mode this stays capped by `GOVA_PERF_REAL_LLM_MAX_MESSAGES`.
- Raise `GOVA_PERF_CONCURRENCY` to model more parallel model calls; watch for
  provider rate limits.
- Lower `GOVA_PERF_MODEL_LATENCY_MS` to isolate pipeline overhead, or raise it to
  model a slower provider without paying for calls.
- Tighten `GOVA_PERF_LATENCY_BUDGET_MS` to catch latency regressions. The
  default is 250 ms for stubbed runs and 1000 ms for real-LLM runs; the measured
  real p99 of 544.50 ms leaves headroom under the latter.
