#!/usr/bin/env python3
"""Estimate heart rate (BPM) from a PPG capture exported by SensorLab.

The sample rate must be well above 8 Hz (twice the 4 Hz upper edge of the
pulse band) for the band-pass filter to be valid.

Example
-------
    python heart_rate.py ../data/ppg.csv --units mV --plot ppg.png
"""

from __future__ import annotations

import argparse

import matplotlib.pyplot as plt

from sensorlab import estimate_heart_rate, load_capture
from sensorlab.signal import PPG_BAND_HZ


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", help="CSV/Excel file exported from SensorLab")
    p.add_argument("--time-col")
    p.add_argument("--value-col")
    p.add_argument("--units", default="mV", help="label for the raw signal axis")
    p.add_argument("--low", type=float, default=PPG_BAND_HZ[0], help="band-pass low edge (Hz)")
    p.add_argument("--high", type=float, default=PPG_BAND_HZ[1], help="band-pass high edge (Hz)")
    p.add_argument("--max-bpm", type=float, default=200.0, help="refractory limit for peak detection")
    p.add_argument("--plot", help="save a diagnostic figure to this path")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    cap = load_capture(args.csv, args.time_col, args.value_col)
    res = estimate_heart_rate(cap.t, cap.y, band_hz=(args.low, args.high), max_bpm=args.max_bpm)

    print(f"source        : {cap.source.name}")
    print(f"samples       : {cap.t.size} over {cap.duration_s:.1f} s (fs ~ {cap.sample_rate_hz:.3g} Hz)")
    print(f"beats detected: {res.peak_times_s.size}")
    print(f"heart rate    : {res.bpm:.1f} BPM (median RR {1e3 * 60 / res.bpm:.0f} ms)")
    print(f"RR variability: {res.rr_std_ms:.1f} ms (SD)")

    if args.plot:
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 6), constrained_layout=True)
        ax1.plot(cap.t, cap.y, lw=0.9)
        ax1.set(ylabel=f"Raw ({args.units})", title=f"PPG capture: {res.bpm:.1f} BPM")
        ax2.plot(cap.t, res.filtered, lw=0.9, label=f"band-pass {args.low}–{args.high} Hz")
        ax2.plot(res.peak_times_s, res.filtered[res.peak_indices], "rv", ms=5, label="detected beats")
        ax2.set(xlabel="Time (s)", ylabel="Filtered")
        ax2.legend(fontsize=8)
        for ax in (ax1, ax2):
            ax.grid(alpha=0.3)
        fig.savefig(args.plot, dpi=150)
        print(f"saved {args.plot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
