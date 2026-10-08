"""Loading of time-series captures exported by the SensorLab software.

The on-device "Download Excel" button saves a CSV (e.g. ``data (1).csv``)
holding a time column and one or more sample columns. Column names vary
between module pages, so the loader detects them unless they are given.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Capture:
    """A single-channel capture with time in seconds from the first sample."""

    t: np.ndarray
    y: np.ndarray
    time_label: str
    value_label: str
    source: Path

    @property
    def duration_s(self) -> float:
        return float(self.t[-1] - self.t[0]) if self.t.size > 1 else 0.0

    @property
    def sample_rate_hz(self) -> float:
        """Median-interval sample rate, robust to occasional dropped samples."""
        if self.t.size < 2:
            raise ValueError("need at least two samples to infer a sample rate")
        dt = np.median(np.diff(self.t))
        if dt <= 0:
            raise ValueError("time column is not strictly increasing")
        return float(1.0 / dt)


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xls", ".xlsx"}:
        return pd.read_excel(path)
    return pd.read_csv(path, sep=None, engine="python")  # sniff , ; or tab


def _numeric_fraction(col: pd.Series) -> float:
    """Share of non-empty cells that parse as numbers (blank cells are ignored)."""
    present = col.dropna()
    if present.empty:
        return 0.0
    return float(pd.to_numeric(present, errors="coerce").notna().mean())


def _to_seconds(col: pd.Series) -> np.ndarray:
    if _numeric_fraction(col) > 0.9:
        values = pd.to_numeric(col, errors="coerce").to_numpy(dtype=float)
    else:
        stamps = pd.to_datetime(col.astype(str), errors="coerce", format="mixed")
        if stamps.notna().mean() < 0.9:
            raise ValueError(f"column {col.name!r} is neither numeric nor a timestamp")
        values = (stamps - stamps.dropna().iloc[0]).dt.total_seconds().to_numpy()
    return values - np.nanmin(values)


def load_capture(path, time_col: str | None = None, value_col: str | None = None) -> Capture:
    """Load a capture, auto-detecting the time and value columns.

    If no column is named, the first column is taken as time and the first
    remaining mostly-numeric column as the value. Rows with missing values
    are dropped and the result is sorted by time.
    """
    path = Path(path)
    df = _read_table(path)
    if df.shape[1] < 2:
        raise ValueError(f"{path.name}: expected at least two columns, found {df.shape[1]}")

    time_col = time_col or df.columns[0]
    if value_col is None:
        candidates = [
            c for c in df.columns if c != time_col and _numeric_fraction(df[c]) > 0.9
        ]
        if not candidates:
            raise ValueError(f"{path.name}: no numeric value column found")
        value_col = candidates[0]

    t = _to_seconds(df[time_col])
    y = pd.to_numeric(df[value_col], errors="coerce").to_numpy(dtype=float)
    keep = np.isfinite(t) & np.isfinite(y)
    order = np.argsort(t[keep], kind="stable")
    return Capture(
        t=t[keep][order],
        y=y[keep][order],
        time_label=str(time_col),
        value_label=str(value_col),
        source=path,
    )
