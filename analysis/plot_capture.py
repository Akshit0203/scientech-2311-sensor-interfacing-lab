#!/usr/bin/env python3
"""Plot a SensorLab capture, optionally converting raw volts to engineering units.

Examples
--------
    python plot_capture.py ../data/lm35.csv --convert lm35 --units V -o lm35.png
    python plot_capture.py ../data/ir.csv --smooth 5 --title "SS03 phototransistor Vout"
"""

from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import numpy as np

from sensorlab import load_capture, moving_average
from sensorlab.models import lm35_voltage_to_celsius

UNIT_SCALE = {"V": 1.0, "mV": 1e-3}


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", help="CSV/Excel file exported from SensorLab")
    p.add_argument("--time-col", help="name of the time column (default: first column)")
    p.add_argument("--value-col", help="name of the value column (default: first numeric column)")
    p.add_argument("--units", choices=UNIT_SCALE, default="V", help="units of the raw value column")
    p.add_argument("--convert", choices=["none", "lm35"], default="none", help="convert volts to °C")
    p.add_argument("--gain", type=float, default=1.0, help="amplifier gain ahead of the ADC")
    p.add_argument("--smooth", type=int, default=1, help="moving-average window in samples")
    p.add_argument("--title", help="figure title")
    p.add_argument("-o", "--output", help="save the figure here instead of showing it")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    cap = load_capture(args.csv, args.time_col, args.value_col)
    y = cap.y

    if args.convert == "lm35":
        y = lm35_voltage_to_celsius(y * UNIT_SCALE[args.units], gain=args.gain)
        ylabel = "Temperature (°C)"
    else:
        ylabel = f"{cap.value_label} ({args.units})"

    y_s = moving_average(y, args.smooth)

    fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)
    if args.smooth > 1:
        ax.plot(cap.t, y, color="0.75", lw=0.8, label="raw")
    ax.plot(cap.t, y_s, lw=1.4, label=f"MA({args.smooth})" if args.smooth > 1 else "signal")
    i_max, i_min = int(np.argmax(y_s)), int(np.argmin(y_s))
    for i, tag in ((i_max, "max"), (i_min, "min")):
        ax.annotate(f"{tag} {y_s[i]:.3g}", (cap.t[i], y_s[i]), textcoords="offset points",
                    xytext=(6, 6), fontsize=8)
    ax.set(xlabel="Time (s)", ylabel=ylabel, title=args.title or cap.source.name)
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8)

    print(f"{cap.source.name}: {cap.t.size} samples, {cap.duration_s:.1f} s, "
          f"fs ~ {cap.sample_rate_hz:.3g} Hz, min {y.min():.4g}, max {y.max():.4g}, mean {y.mean():.4g}")

    if args.output:
        fig.savefig(args.output, dpi=150)
        print(f"saved {args.output}")
    else:
        plt.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
