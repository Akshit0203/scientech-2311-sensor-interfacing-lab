# SensorLab Analysis Toolkit

A small, tested Python package for **offline analysis of captures exported from the Scientech 2311 SensorLab** (`Download Excel` → CSV). It reproduces the lab calculations: unit conversion, sensor linearisation, filtering and heart-rate extraction.

## Installation

```bash
cd analysis
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Requires Python ≥ 3.10.

## Command-Line Tools

### `plot_capture.py`: plot any capture

```bash
python plot_capture.py ../data/raw/lm35.csv --convert lm35 --units V -o lm35.png
python plot_capture.py ../data/raw/ir.csv --smooth 5 --title "SS03 phototransistor Vout"
```

| Option | Description |
|--------|-------------|
| `--time-col`, `--value-col` | Column names (auto-detected by default) |
| `--units {V,mV}` | Units of the raw value column |
| `--convert {none,lm35}` | Convert volts to °C using 10 mV/°C |
| `--gain` | Gain of any amplifier between the sensor and the ADC |
| `--smooth N` | Centred moving average over N samples |
| `-o PATH` | Save the figure instead of opening a window |

### `heart_rate.py`: estimate BPM from a PPG capture

```bash
python heart_rate.py ../data/raw/ppg.csv --units mV --plot ppg.png
```

Example output (synthetic 78 BPM test signal, 50 Hz):

```
source        : ppg.csv
samples       : 1500 over 30.0 s (fs ~ 50 Hz)
beats detected: 39
heart rate    : 78.9 BPM (median RR 760 ms)
RR variability: 10.1 ms (SD)
```

Pipeline: **sample-rate inference → zero-phase Butterworth band-pass (0.5–4 Hz) → peak detection with a refractory period → 60 / median(RR)**. The capture must be sampled well above 8 Hz.

## Library API

```python
from sensorlab import load_capture, estimate_heart_rate
from sensorlab import models as m

cap = load_capture("../data/raw/lm35.csv")          # Capture(t, y, labels, source)
temp_c = m.lm35_voltage_to_celsius(cap.y, gain=1)   # volts → °C

r_ntc = m.divider_sensor_resistance(v_out=2.1, r_fixed=10_000, v_in=5.0)
t_ntc = m.ntc_temperature(r_ntc, r0=4_700, beta=3_950)

a, b, c = m.steinhart_hart_coefficients([(0, 15_800), (25, 4_700), (50, 1_690)])
```

### `sensorlab.models`

| Function | Equation |
|----------|----------|
| `lm35_voltage_to_celsius`, `celsius_to_lm35_voltage` | T = V / (G · 10 mV/°C) |
| `divider_output`, `divider_sensor_resistance` | V = V<sub>in</sub> · R<sub>bottom</sub> / (R<sub>top</sub> + R<sub>bottom</sub>) |
| `ntc_resistance`, `ntc_temperature` | β-model |
| `steinhart_hart_coefficients`, `steinhart_hart_temperature` | 1/T = A + B ln R + C (ln R)³ |
| `pt100_resistance`, `pt100_temperature` | Callendar–Van Dusen (IEC 60751) |
| `non_inverting_gain`, `inverting_gain`, `instrumentation_amp_gain` | Op-amp gain equations |
| `rc_cutoff_hz` | f<sub>c</sub> = 1 / 2πRC |
| `adc_lsb`, `adc_code_to_voltage`, `voltage_to_adc_code` | Ideal N-bit quantiser |

### `sensorlab.capture`

`load_capture(path, time_col=None, value_col=None)` reads CSV (delimiter sniffed) or Excel. It accepts numeric or clock-style (`22:20:39`) time columns and converts them to seconds from the first sample. It drops incomplete rows and sorts by time. `Capture.sample_rate_hz` uses the median sample interval, so a few dropped samples don't skew it.

### `sensorlab.signal`

`moving_average`, `bandpass` (zero-phase SOS Butterworth), and `estimate_heart_rate`, which returns `HeartRateResult(bpm, peak_indices, peak_times_s, rr_intervals_s, filtered, rr_std_ms)`.

## Tests

```bash
python -m pytest
```

The tests check against **IEC 60751 PT100 table values**, the kit's **0.385 Ω/°C** RTD coefficient, the **LM35 readings recorded in the lab** (35.8 °C and 37.4 °C), round-trips of every forward/inverse model, and heart-rate recovery on synthetic PPG signals with baseline wander and noise at 55, 72 and 110 BPM.
