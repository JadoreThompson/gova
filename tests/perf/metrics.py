from __future__ import annotations

import math


def percentile(sorted_values: list[float], fraction: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]

    rank = (len(sorted_values) - 1) * fraction
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return sorted_values[lower]

    weight = rank - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def latency_percentiles(latencies_ms: list[float]) -> dict[str, float]:
    ordered = sorted(latencies_ms)
    return {
        f"p{int(fraction * 100)}": percentile(ordered, fraction)
        for fraction in (0.5, 0.9, 0.95, 0.99)
    }


def format_percentiles(percentiles: dict[str, float]) -> str:
    return ", ".join(f"{name}={value:.2f}ms" for name, value in percentiles.items())
