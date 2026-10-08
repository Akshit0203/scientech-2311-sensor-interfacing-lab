import numpy as np
import pytest

from sensorlab import models as m


def test_lm35_observed_lab_values():
    # Readings from the LM35 session: 35.8 °C start, 37.4 °C peak.
    assert m.lm35_voltage_to_celsius(0.358) == pytest.approx(35.8)
    assert m.lm35_voltage_to_celsius(0.374) == pytest.approx(37.4)


def test_lm35_with_gain_round_trip():
    temps = np.array([-10.0, 0.0, 25.0, 100.0])
    v = m.celsius_to_lm35_voltage(temps, gain=3.3)
    np.testing.assert_allclose(m.lm35_voltage_to_celsius(v, gain=3.3), temps)


def test_lm35_rejects_non_positive_gain():
    with pytest.raises(ValueError):
        m.lm35_voltage_to_celsius(0.25, gain=0)


@pytest.mark.parametrize("sensor_on_top", [False, True])
def test_divider_round_trip(sensor_on_top):
    r = np.array([500.0, 4_700.0, 50_000.0])
    v = m.divider_output(r, r_fixed=10_000.0, v_in=5.0, sensor_on_top=sensor_on_top)
    np.testing.assert_allclose(
        m.divider_sensor_resistance(v, 10_000.0, 5.0, sensor_on_top=sensor_on_top), r
    )


def test_divider_rejects_rail_voltages():
    with pytest.raises(ValueError):
        m.divider_sensor_resistance(5.0, 10_000.0, 5.0)


def test_ntc_nominal_point_and_monotonic():
    assert m.ntc_resistance(25.0) == pytest.approx(4_700.0)
    temps = np.linspace(0, 100, 11)
    r = m.ntc_resistance(temps)
    assert np.all(np.diff(r) < 0), "NTC resistance must fall as temperature rises"
    np.testing.assert_allclose(m.ntc_temperature(r), temps, atol=1e-9)


def test_steinhart_hart_recovers_beta_curve():
    pts = [(t, float(m.ntc_resistance(t))) for t in (0.0, 25.0, 50.0)]
    a, b, c = m.steinhart_hart_coefficients(pts)
    for t, r in pts:
        assert m.steinhart_hart_temperature(r, a, b, c) == pytest.approx(t, abs=1e-6)
    # Interpolation between calibration points stays within 0.1 °C of the β model.
    assert m.steinhart_hart_temperature(m.ntc_resistance(37.0), a, b, c) == pytest.approx(37.0, abs=0.1)


def test_pt100_reference_values():
    # IEC 60751 table values.
    assert m.pt100_resistance(0.0) == pytest.approx(100.0)
    assert m.pt100_resistance(100.0) == pytest.approx(138.5055, abs=1e-3)
    assert m.pt100_resistance(-100.0) == pytest.approx(60.2558, abs=1e-3)
    assert m.pt100_temperature(138.5055) == pytest.approx(100.0, abs=1e-3)


def test_pt100_mean_slope_matches_kit_panel():
    # Kit panel: "100 Ω at 0 °C, coefficient 0.385 Ω/°C" (mean slope over 0–100 °C).
    slope = (m.pt100_resistance(100.0) - m.pt100_resistance(0.0)) / 100.0
    assert slope == pytest.approx(0.385, abs=1e-3)


def test_amplifier_and_filter_equations():
    assert m.non_inverting_gain(9_000, 1_000) == pytest.approx(10.0)
    assert m.inverting_gain(10_000, 1_000) == pytest.approx(-10.0)
    assert m.instrumentation_amp_gain(r_gain=1_000, r_internal=24_500) == pytest.approx(50.0)
    assert m.rc_cutoff_hz(10_000, 100e-9) == pytest.approx(159.155, rel=1e-4)


def test_adc_quantisation():
    assert m.adc_lsb(3.3, 12) == pytest.approx(3.3 / 4096)
    codes = m.voltage_to_adc_code([-0.1, 0.0, 1.65, 3.3, 5.0], v_ref=3.3, bits=12)
    assert codes.tolist() == [0, 0, 2048, 4095, 4095]
    assert m.adc_code_to_voltage(2048, 3.3, 12) == pytest.approx(1.65)
