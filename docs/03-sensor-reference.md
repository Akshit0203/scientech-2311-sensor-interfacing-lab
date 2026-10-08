# Sensor Reference

Parameters marked **(kit)** are taken from the Scientech 2311 front panel and module pages. Others are typical values from the manufacturers' datasheets. Always confirm them against the datasheet of the exact part you use.

---

## Temperature Sensors

### LM35: Precision Centigrade Temperature Sensor

| Parameter | Value |
|-----------|-------|
| Output | Linear voltage, **10 mV/°C (kit)** |
| Range | −55 °C to +150 °C |
| Accuracy | ±0.5 °C at 25 °C (typ.) |
| Supply | 4–30 V |
| Quiescent current | ≈ 60 µA, giving < 0.1 °C self-heating in still air |
| Pinout (TO-92, flat face toward you) | 1: +V<sub>S</sub> · 2: V<sub>OUT</sub> · 3: GND |
| Transfer function | $T = V_{out}/10\ \text{mV}$ |

### NTC Thermistor

| Parameter | Value |
|-----------|-------|
| R<sub>25</sub> | **4.7 kΩ (kit)** |
| β (B25/85) | ≈ 3500–4000 K (part-dependent; toolkit default 3950 K) |
| Model | β-equation or Steinhart–Hart |
| Characteristic | Strongly non-linear, ≈ −4 %/°C near 25 °C |

### Platinum RTD (PT100)

| Parameter | Value |
|-----------|-------|
| R<sub>0</sub> | **100 Ω at 0 °C (kit)** |
| Mean coefficient | **0.385 Ω/°C (kit)** (α = 0.00385 /°C, IEC 60751) |
| Model (T ≥ 0 °C) | $R = R_0(1 + AT + BT^2)$, A = 3.9083×10⁻³, B = −5.775×10⁻⁷ |
| Model (T < 0 °C) | adds $C(T-100)T^3$, C = −4.183×10⁻¹² |

### K-type Thermocouple

| Parameter | Value |
|-----------|-------|
| Range | **−200 °C to +1250 °C (kit)** |
| Sensitivity | ≈ 41 µV/°C |
| Requirement | Instrumentation amplifier and cold-junction compensation (LM35_Cold on SS01) |

### AD590: Current-Output Temperature Transducer

| Parameter | Value |
|-----------|-------|
| Output | 1 µA/K (298.2 µA at 25 °C) |
| Advantage | Current output, so it is immune to lead resistance over long cables |

---

## Optical Sensors

### Light-Dependent Resistor (LDR)

| Parameter | Value |
|-----------|-------|
| Material | CdS photoconductor |
| Behaviour | **Resistance decreases as light intensity increases (kit)** |
| Dark / light resistance | ~1 MΩ / ~1–10 kΩ (typ.) |
| Response time | Tens of ms (rise), longer decay |
| Spectral peak | ≈ 540 nm (green, close to the human eye) |

### BPX65: PIN Photodiode

| Parameter | Value |
|-----------|-------|
| Application range | **500–1100 nm (kit)** |
| Spectral peak | ≈ 850 nm |
| Mode | Reverse-biased (photoconductive) for speed and linearity |
| Response | ns-scale, linear photocurrent vs irradiance |

### L14F1: NPN Photo-Darlington

| Parameter | Value |
|-----------|-------|
| Application range | **500–1100 nm (kit)** |
| Gain | Very high (Darlington), mA-level output at modest irradiance |
| Trade-off | Slower and less linear than a photodiode, saturates easily |

### Photovoltaic Cell

| Parameter | Value |
|-----------|-------|
| Principle | **Produces a potential difference according to the light intensity (kit)** |
| Open-circuit voltage | Logarithmic in irradiance |
| Short-circuit current | Linear in irradiance |

---

## Infrared Devices

### IR LED + Phototransistor Pair (SS03)

| Parameter | Value |
|-----------|-------|
| Emitter series resistor | **500 Ω (kit)**, I<sub>F</sub> ≈ 7.6 mA at 5 V |
| Receiver load | **10 kΩ pull-up (kit)** |
| Logic | Clear path → High, IR incident → transistor ON → Low |
| Emission characteristic | Radiant intensity ∝ forward current (0–100 mA) |

### TSOP1738: IR Receiver Module

| Parameter | Value |
|-----------|-------|
| Carrier | **38 kHz (kit)** |
| Internals | Photodiode, AGC, band-pass filter, demodulator |
| Output | Active-low, open-collector-style digital |
| Applications | **Remote control, reference positioning system, object counter (kit)** |

---

## Biomedical

### Optical Heart-Rate (PPG) Sensor

| Parameter | Value |
|-----------|-------|
| Principle | Reflective photoplethysmography |
| Supply | ±5 V and GND (module pins) |
| Signal | Small pulsatile AC (~1 %) on a large DC level |
| Band of interest | 0.5–4 Hz |

---

## Other Sensors on the Platform (not covered in these experiments)

| Sensor | Notes |
|--------|-------|
| **Ultrasonic TX/RX** | 40 kHz transducer pair, used as a distance meter or proximity switch (kit) |
