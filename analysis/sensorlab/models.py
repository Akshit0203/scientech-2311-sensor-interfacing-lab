"""Sensor transfer functions and front-end design equations.

Every function accepts scalars or NumPy arrays and returns the same shape,
so a whole capture can be converted in one call.

Units are SI unless the parameter name says otherwise
(volts, ohms, farads, hertz, degrees Celsius).
"""

from __future__ import annotations

import numpy as np

KELVIN_OFFSET = 273.15

# --------------------------------------------------------------------------- #
# LM35 precision temperature sensor
# --------------------------------------------------------------------------- #
LM35_SCALE_V_PER_C = 0.010  # 10 mV/°C
LM35_RANGE_C = (-55.0, 150.0)


def lm35_voltage_to_celsius(v_out, gain: float = 1.0):
    """Convert LM35 output voltage to temperature.

    T(°C) = V_out / (gain * 10 mV/°C)

    Parameters
    ----------
    v_out : volts measured at the ADC.
    gain  : voltage gain of any amplifier stage between the LM35 and the ADC.
    """
    if gain <= 0:
        raise ValueError("gain must be positive")
    return np.asarray(v_out, dtype=float) / (gain * LM35_SCALE_V_PER_C)


def celsius_to_lm35_voltage(temp_c, gain: float = 1.0):
    """Expected LM35 output (volts) for a given temperature."""
    return np.asarray(temp_c, dtype=float) * LM35_SCALE_V_PER_C * gain


# --------------------------------------------------------------------------- #
# Resistive sensors in a voltage divider (LDR, NTC, RTD)
# --------------------------------------------------------------------------- #
def divider_output(r_sensor, r_fixed: float, v_in: float, sensor_on_top: bool = False):
    """Output voltage of a two-resistor divider.

    sensor_on_top=False : V_in -- R_fixed -- (V_out) -- R_sensor -- GND
    sensor_on_top=True  : V_in -- R_sensor -- (V_out) -- R_fixed -- GND
    """
    r_sensor = np.asarray(r_sensor, dtype=float)
    lower = r_fixed if sensor_on_top else r_sensor
    return v_in * lower / (r_sensor + r_fixed)


def divider_sensor_resistance(v_out, r_fixed: float, v_in: float, sensor_on_top: bool = False):
    """Invert :func:`divider_output` to recover the sensor resistance."""
    v_out = np.asarray(v_out, dtype=float)
    if np.any((v_out <= 0) | (v_out >= v_in)):
        raise ValueError("v_out must lie strictly between 0 and v_in")
    if sensor_on_top:
        return r_fixed * (v_in - v_out) / v_out
    return r_fixed * v_out / (v_in - v_out)


# --------------------------------------------------------------------------- #
# NTC thermistor
# --------------------------------------------------------------------------- #
NTC_R25_OHM = 4_700.0  # SS01 module thermistor (kit panel: "NTC Thermistor 4.7 kΩ")
NTC_BETA_DEFAULT = 3_950.0  # typical value; confirm against the part's datasheet


def ntc_resistance(temp_c, r0: float = NTC_R25_OHM, t0_c: float = 25.0, beta: float = NTC_BETA_DEFAULT):
    """β-model: R(T) = R0 · exp(β · (1/T − 1/T0))."""
    t = np.asarray(temp_c, dtype=float) + KELVIN_OFFSET
    t0 = t0_c + KELVIN_OFFSET
    return r0 * np.exp(beta * (1.0 / t - 1.0 / t0))


def ntc_temperature(r_ohm, r0: float = NTC_R25_OHM, t0_c: float = 25.0, beta: float = NTC_BETA_DEFAULT):
    """Inverse β-model: 1/T = 1/T0 + ln(R/R0)/β."""
    r = np.asarray(r_ohm, dtype=float)
    inv_t = 1.0 / (t0_c + KELVIN_OFFSET) + np.log(r / r0) / beta
    return 1.0 / inv_t - KELVIN_OFFSET


def steinhart_hart_temperature(r_ohm, a: float, b: float, c: float):
    """Steinhart–Hart: 1/T = A + B·ln(R) + C·ln(R)³ (T in kelvin)."""
    ln_r = np.log(np.asarray(r_ohm, dtype=float))
    return 1.0 / (a + b * ln_r + c * ln_r**3) - KELVIN_OFFSET


def steinhart_hart_coefficients(points):
    """Solve A, B, C from three (temperature °C, resistance Ω) calibration points."""
    if len(points) != 3:
        raise ValueError("exactly three calibration points are required")
    t = np.array([p[0] for p in points], dtype=float) + KELVIN_OFFSET
    ln_r = np.log(np.array([p[1] for p in points], dtype=float))
    m = np.column_stack([np.ones(3), ln_r, ln_r**3])
    a, b, c = np.linalg.solve(m, 1.0 / t)
    return float(a), float(b), float(c)


# --------------------------------------------------------------------------- #
# Platinum RTD (PT100, IEC 60751 / Callendar–Van Dusen)
# --------------------------------------------------------------------------- #
PT100_R0 = 100.0
CVD_A = 3.9083e-3
CVD_B = -5.775e-7
CVD_C = -4.183e-12  # applies below 0 °C only


def pt100_resistance(temp_c, r0: float = PT100_R0):
    """Callendar–Van Dusen resistance of a platinum RTD."""
    t = np.asarray(temp_c, dtype=float)
    base = 1.0 + CVD_A * t + CVD_B * t**2
    cold = CVD_C * (t - 100.0) * t**3
    return r0 * (base + np.where(t < 0, cold, 0.0))


def pt100_temperature(r_ohm, r0: float = PT100_R0):
    """Closed-form inverse of Callendar–Van Dusen for T ≥ 0 °C."""
    r = np.asarray(r_ohm, dtype=float)
    disc = CVD_A**2 - 4.0 * CVD_B * (1.0 - r / r0)
    return (-CVD_A + np.sqrt(disc)) / (2.0 * CVD_B)


# --------------------------------------------------------------------------- #
# Op-amp stages and filters on the base board
# --------------------------------------------------------------------------- #
def non_inverting_gain(r_feedback: float, r_ground: float) -> float:
    """A_v = 1 + R_f / R_g."""
    return 1.0 + r_feedback / r_ground


def inverting_gain(r_feedback: float, r_input: float) -> float:
    """A_v = −R_f / R_in."""
    return -r_feedback / r_input


def instrumentation_amp_gain(r_gain: float, r_internal: float) -> float:
    """Classic three-op-amp INA: A_v = 1 + 2·R / R_G (unity-gain difference stage)."""
    return 1.0 + 2.0 * r_internal / r_gain


def rc_cutoff_hz(r_ohm: float, c_farad: float) -> float:
    """First-order RC corner frequency f_c = 1 / (2π·R·C)."""
    return 1.0 / (2.0 * np.pi * r_ohm * c_farad)


# --------------------------------------------------------------------------- #
# ADC quantisation
# --------------------------------------------------------------------------- #
def adc_lsb(v_ref: float, bits: int) -> float:
    """Voltage weight of one LSB: V_ref / 2^N."""
    return v_ref / (1 << bits)


def adc_code_to_voltage(code, v_ref: float, bits: int):
    return np.asarray(code, dtype=float) * adc_lsb(v_ref, bits)


def voltage_to_adc_code(v, v_ref: float, bits: int):
    """Ideal quantiser with clipping to [0, 2^N − 1]."""
    codes = np.floor(np.asarray(v, dtype=float) / adc_lsb(v_ref, bits))
    return np.clip(codes, 0, (1 << bits) - 1).astype(int)
