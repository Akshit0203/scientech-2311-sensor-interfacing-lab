# Signal Conditioning and ADC Interfacing

Raw sensor outputs are rarely ADC-ready. They may be too small (thermocouple µV, LM35 mV), too high-impedance (dividers, phototransistor loads), noisy, or riding on a large DC offset (PPG). This document collects the design equations behind the base-board blocks used in the experiments. Each equation has a matching function in [`analysis/sensorlab/models.py`](../analysis/sensorlab/models.py).

---

## 1. Conditioning Chain

```
Sensor ─▶ Excitation/Bias ─▶ Buffer ─▶ Gain ─▶ Filter ─▶ (Offset/level shift) ─▶ ADC
            divider          high-Z     match     anti-alias        fit 0…V_ref
            pull-up          isolate    span      reject noise
```

**Design goal:** map the sensor's *useful* output range onto the ADC's *full* input range, with the bandwidth limited to what the measurement actually needs.

## 2. Excitation Networks

### Voltage divider (LDR, NTC, RTD)

$$V_{out} = V_{in}\,\frac{R_{bottom}}{R_{top} + R_{bottom}}
\qquad\Longrightarrow\qquad
R_{sensor,\ bottom} = R_{fixed}\,\frac{V_{out}}{V_{in} - V_{out}}$$

Sensitivity is highest when R<sub>fixed</sub> ≈ R<sub>sensor</sub> at the centre of the range of interest. For a 4.7 kΩ NTC near 25 °C, a **4.7 kΩ–10 kΩ** fixed resistor is appropriate.

`models.divider_output()`, `models.divider_sensor_resistance()`

### Pull-up load (phototransistor)

$$V_{out} = V_{CC} - I_C R_L$$

R<sub>L</sub> trades sensitivity against the onset of saturation (V<sub>CE(sat)</sub> ≈ 0.2 V).

### LED current limiting (IR emitter)

$$R = \frac{V_{CC} - V_F}{I_F}$$

On SS03: 500 Ω at 5 V with V<sub>F</sub> ≈ 1.2 V gives I<sub>F</sub> ≈ 7.6 mA.

## 3. Amplifiers

| Topology | Gain | Input impedance | Use |
|----------|------|-----------------|-----|
| Non-inverting | $1 + R_f/R_g$ | Very high | Scaling single-ended sensor voltages |
| Inverting | $-R_f/R_{in}$ | R<sub>in</sub> | Inversion, summing, offset |
| Differential | $\frac{R_f}{R_{in}}(V_2 - V_1)$ | Moderate | Simple bridges |
| Instrumentation (3-op-amp) | $1 + 2R/R_G$ | Very high, both inputs | Thermocouples, bridges, high CMRR |
| Buffer | 1 | Very high | Impedance isolation before the ADC |

`models.non_inverting_gain()`, `models.inverting_gain()`, `models.instrumentation_amp_gain()`

**Worked example (LM35):** to map 0–50 °C (0–500 mV) onto a 0–5 V input, choose A<sub>v</sub> = 10 → R<sub>f</sub> = 9 kΩ, R<sub>g</sub> = 1 kΩ.

## 4. Filters

First-order RC corner frequency:

$$f_c = \frac{1}{2\pi RC}$$

| Measurement | Signal band | Recommended filtering |
|-------------|-------------|-----------------------|
| Temperature (LM35 / NTC) | < 0.1 Hz | Low-pass, f<sub>c</sub> ≈ 1–10 Hz, plus 0.1 µF at the sensor |
| Light (LDR, phototransistor) | DC–10 Hz | Low-pass to reject 100 Hz lamp flicker |
| IR proximity (DC-coupled) | DC–100 Hz | Low-pass. Use a 38 kHz band-pass if modulated |
| PPG / heart rate | 0.5–4 Hz | **Band-pass**: high-pass for baseline, low-pass for noise |

`models.rc_cutoff_hz()`, `signal.bandpass()` (digital zero-phase Butterworth)

## 5. ADC Fundamentals

| Quantity | Expression |
|----------|------------|
| LSB size | $\text{LSB} = V_{ref} / 2^N$ |
| Code → voltage | $V = \text{code} \times \text{LSB}$ |
| Quantisation noise (RMS) | $\text{LSB}/\sqrt{12}$ |
| Ideal SNR | $6.02N + 1.76\ \text{dB}$ |
| Nyquist criterion | $f_s > 2 f_{max}$ (in practice 5–10×) |

**Example:** a 12-bit ADC with V<sub>ref</sub> = 3.3 V has an LSB of 0.806 mV. An LM35 without gain then resolves ≈ 0.08 °C per code. With A<sub>v</sub> = 10 that improves to ≈ 0.008 °C, so sensor accuracy (±0.5 °C typ.), not the ADC, becomes the limit.

`models.adc_lsb()`, `models.adc_code_to_voltage()`, `models.voltage_to_adc_code()`

## 6. Sampling-Rate Choice

| Measurement | Bandwidth | Adequate f<sub>s</sub> |
|-------------|-----------|------------------------|
| Temperature | < 0.1 Hz | 1 Hz (as used on the SensorLab temperature pages) |
| Light / IR proximity | ≤ 10 Hz | 50–100 Hz |
| PPG heart rate | ≤ 4 Hz (harmonics to ~10 Hz) | **≥ 50 Hz** |

## 7. Good Practice Checklist

- [ ] Common ground between module, base board and ADC
- [ ] Decoupling capacitor (0.1 µF) at each sensor supply pin
- [ ] Short, twisted signal and ground leads for low-level signals
- [ ] Buffer high-impedance sources before the ADC
- [ ] Anti-alias low-pass below f<sub>s</sub>/2
- [ ] Gain set so the maximum expected signal reaches ~80–90 % of full scale (headroom without clipping)
- [ ] Record gain settings alongside each capture so the volts can be converted back to physical units
