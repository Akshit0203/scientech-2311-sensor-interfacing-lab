"""Signal-processing helpers for sensor captures."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, find_peaks, sosfiltfilt

# Physiological pulse band: 30–240 BPM.
PPG_BAND_HZ = (0.5, 4.0)


def moving_average(y, window: int):
    """Centred moving average with edge-preserving 'same' length output."""
    if window < 1:
        raise ValueError("window must be >= 1")
    y = np.asarray(y, dtype=float)
    if window == 1:
        return y.copy()
    kernel = np.ones(window) / window
    padded = np.pad(y, (window // 2, window - 1 - window // 2), mode="edge")
    return np.convolve(padded, kernel, mode="valid")


def bandpass(y, fs: float, low_hz: float, high_hz: float, order: int = 2):
    """Zero-phase Butterworth band-pass (no group delay, so peaks keep their timing)."""
    nyq = fs / 2.0
    if not 0 < low_hz < high_hz:
        raise ValueError("require 0 < low_hz < high_hz")
    if high_hz >= nyq:
        raise ValueError(f"high_hz ({high_hz}) must be below Nyquist ({nyq:.3g} Hz)")
    sos = butter(order, [low_hz / nyq, high_hz / nyq], btype="bandpass", output="sos")
    return sosfiltfilt(sos, np.asarray(y, dtype=float))


@dataclass(frozen=True)
class HeartRateResult:
    bpm: float
    peak_indices: np.ndarray
    peak_times_s: np.ndarray
    rr_intervals_s: np.ndarray
    filtered: np.ndarray

    @property
    def rr_std_ms(self) -> float:
        """SDNN-style variability of the detected beat-to-beat intervals."""
        return float(np.std(self.rr_intervals_s, ddof=1) * 1e3) if self.rr_intervals_s.size > 1 else 0.0


def estimate_heart_rate(
    t,
    y,
    band_hz: tuple[float, float] = PPG_BAND_HZ,
    max_bpm: float = 200.0,
    prominence: float | None = None,
) -> HeartRateResult:
    """Estimate heart rate from a PPG waveform.

    1. Infer the sample rate from the median sample interval.
    2. Band-pass to the pulse band to remove baseline wander and HF noise.
    3. Detect systolic peaks with a refractory distance set by ``max_bpm``.
    4. BPM = 60 / median(RR), which is robust to a missed or extra beat.
    """
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)
    if t.size != y.size or t.size < 3:
        raise ValueError("t and y must have equal length >= 3")

    fs = 1.0 / np.median(np.diff(t))
    filtered = bandpass(y, fs, *band_hz)

    min_distance = max(1, int(fs * 60.0 / max_bpm))
    if prominence is None:
        prominence = 0.3 * np.std(filtered)
    peaks, _ = find_peaks(filtered, distance=min_distance, prominence=prominence)
    if peaks.size < 2:
        raise ValueError("fewer than two beats detected; check signal quality or band")

    peak_times = t[peaks]
    rr = np.diff(peak_times)
    return HeartRateResult(
        bpm=float(60.0 / np.median(rr)),
        peak_indices=peaks,
        peak_times_s=peak_times,
        rr_intervals_s=rr,
        filtered=filtered,
    )
