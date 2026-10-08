import numpy as np
import pandas as pd
import pytest

from sensorlab import estimate_heart_rate, load_capture, moving_average
from sensorlab.signal import bandpass


def synthetic_ppg(bpm=72.0, fs=50.0, duration=30.0, seed=0):
    """PPG-like test signal: pulse train plus baseline wander, mains-like HF noise and white noise."""
    rng = np.random.default_rng(seed)
    t = np.arange(0, duration, 1 / fs)
    f = bpm / 60.0
    pulse = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t - 0.8)
    wander = 0.8 * np.sin(2 * np.pi * 0.1 * t)
    hf = 0.2 * np.sin(2 * np.pi * 15 * t)
    y = 600 + 150 * (pulse + wander + hf) + rng.normal(0, 10, t.size)
    return t, y


@pytest.mark.parametrize("bpm", [55.0, 72.0, 110.0])
def test_heart_rate_recovers_synthetic_rate(bpm):
    t, y = synthetic_ppg(bpm=bpm)
    res = estimate_heart_rate(t, y)
    assert res.bpm == pytest.approx(bpm, rel=0.03)
    assert res.peak_indices.size == res.peak_times_s.size
    assert res.rr_std_ms < 50


def test_heart_rate_rejects_flat_signal():
    t = np.arange(0, 10, 0.02)
    with pytest.raises(ValueError):
        estimate_heart_rate(t, np.zeros_like(t))


def test_bandpass_rejects_band_above_nyquist():
    with pytest.raises(ValueError):
        bandpass(np.zeros(100), fs=6.0, low_hz=0.5, high_hz=4.0)


def test_moving_average_preserves_length_and_constants():
    y = np.full(25, 3.0)
    out = moving_average(y, 6)
    assert out.shape == y.shape
    np.testing.assert_allclose(out, 3.0)


def test_load_capture_numeric_time(tmp_path):
    p = tmp_path / "ir.csv"
    pd.DataFrame({"Time": [10, 11, 12, 13], "Voltage": [1.72, 1.0, 0.0, 1.0]}).to_csv(p, index=False)
    cap = load_capture(p)
    np.testing.assert_allclose(cap.t, [0, 1, 2, 3])
    assert cap.value_label == "Voltage"
    assert cap.sample_rate_hz == pytest.approx(1.0)


def test_load_capture_timestamp_time_and_column_selection(tmp_path):
    p = tmp_path / "lm35.csv"
    p.write_text(
        "Time,Label,Temperature\n"
        "22:20:39,a,35.8\n"
        "22:20:40,b,36.1\n"
        "22:20:41,c,\n"
        "22:20:42,d,37.4\n",
        encoding="utf-8",
    )
    cap = load_capture(p)
    assert cap.value_label == "Temperature"
    np.testing.assert_allclose(cap.t, [0, 1, 3])  # row with a missing value dropped
    np.testing.assert_allclose(cap.y, [35.8, 36.1, 37.4])
