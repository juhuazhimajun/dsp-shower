# -*- coding: utf-8 -*-
r"""
生成「听得出混叠」的音频（16bit / 44.1kHz / 单声道）

  A1 扫频_原声.wav            200→7600 Hz 扫频（44.1 kHz）
  A2 扫频_8k采样_无抗混叠.wav  同一个扫频，按 8 kHz 直接取样 → 过 4 kHz 后「折返」
  A3 扫频_先低通再8k采样.wav    先 3.4 kHz 低通再降到 8 kHz → 高频被掐死，不折返
  B1 纯音_6k真身_采样后_2k真身.wav ① 6 kHz ② 6 kHz 过 8 kHz 采样 ③ 真 2 kHz
  C1 星星_原声.wav             14 次谐波的拨弦音色
  C2 星星_2.6k采样_电音.wav     2.6 kHz 采样：1308 Hz 以上谐波折叠 → 金属感
  C3 星星_1.6k采样_重电音.wav   1.6 kHz 采样：Nyquist 只有 800 Hz → 8-bit 破碎感

【关键实现细节】为什么不用「零阶保持」放回 44.1 kHz？
  零阶保持会在 k*fs_low 处产生一堆镜像谱，播放时这些镜像本身就是可听的高频，
  听起来比真实混叠更脏，等于作弊。正确做法是：
    ① 在 fs_low 上「直接按公式取样」——等价于理想 ADC（没有抗混叠滤波）；
    ② 用带限重采样 resample_poly 升回 44.1 kHz——等价于理想 DAC（重建滤波）。
  这样听到的低频成分，就是「混叠折回来」的成分本身，没有额外镜像。

用法： python py\make_audio.py
"""
import json
import os
import wave
from fractions import Fraction

import numpy as np
from scipy.signal import firwin, resample, resample_poly

FS = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "audio"))
os.makedirs(OUT, exist_ok=True)


# ---------------------------------------------------------------- 基础工具
def write_wav(name, x, fs=FS, peak=0.89):
    x = np.asarray(x, dtype=float)
    m = np.max(np.abs(x))
    if m > 0:
        x = x / m * peak
    data = np.round(x * 32767).astype("<i2")
    path = os.path.join(OUT, name)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(fs)
        w.writeframes(data.tobytes())
    return path


def to_playback(y, fs_low):
    """把 fs_low 上的样本带限升采样到 44.1 kHz（模拟理想 DAC 重建）

    用 FFT 重采样（sinc 插值）而不是「零阶保持」或 FIR 插值：
      · 零阶保持会留下 k*fs_low ± f 的镜像，听感比真实混叠更脏；
      · 有限长 FIR 的过渡带太宽，8k−f 的镜像在 5 kHz 附近只压到 −40 dB，
        时频谱上会画出一条「假的高频斜线」，容易误读成「混叠翻到高频去了」。
    FFT 重采样等价于理想砖墙重建滤波，镜像直接被砍干净。
    """
    n_out = int(round(len(y) * FS / float(fs_low)))
    return resample(y, n_out)


def fade(x, fs=FS, ms=15):
    n = int(fs * ms / 1000)
    if n < 2:
        return x
    ramp = np.linspace(0, 1, n)
    x = x.copy()
    x[:n] *= ramp
    x[-n:] *= ramp[::-1]
    return x


def silence(sec, fs=FS):
    return np.zeros(int(sec * fs))


def chirp(f0, f1, dur, fs, phase0=0.0):
    """线性扫频；在任意 fs 上直接按公式取值 = 理想取样"""
    t = np.arange(int(dur * fs)) / fs
    ph = 2 * np.pi * (f0 * t + (f1 - f0) * t ** 2 / (2 * dur)) + phase0
    return np.sin(ph)


# ---------------------------------------------------------------- A. 扫频
def demo_sweep():
    f0, f1, dur = 200.0, 7600.0, 6.0

    write_wav("A1_扫频_原声.wav", fade(chirp(f0, f1, dur, FS), ms=30))

    # 8 kHz 直接取样：4 kHz 以上全部折返 → 音高先升到 4 kHz，再「倒着」滑回来
    low = chirp(f0, f1, dur, 8000)
    write_wav("A2_扫频_8k采样_无抗混叠.wav", fade(to_playback(low, 8000), ms=30))

    # 先低通再降采样：这才是正规 ADC，高频被掐掉，只剩「变闷」
    x = chirp(f0, f1, dur, FS)
    h = firwin(1023, 3400, fs=FS, window=("kaiser", 8.0))
    x_lp = np.convolve(x, h, mode="same")
    dec = resample_poly(x_lp, 80, 441)              # 带限降到 8 kHz
    write_wav("A3_扫频_先低通再8k采样.wav", fade(to_playback(dec, 8000), ms=30))


# ---------------------------------------------------------------- B. 纯音骗局
def demo_pure_tone():
    dur = 0.9
    t_hi = np.arange(int(dur * FS)) / FS

    seg1 = 0.9 * np.sin(2 * np.pi * 6000 * t_hi)            # 6 kHz 原声
    t_lo = np.arange(int(dur * 8000)) / 8000
    seg2 = to_playback(0.9 * np.sin(2 * np.pi * 6000 * t_lo), 8000)  # 采样后 → 2 kHz
    seg3 = 0.9 * np.sin(2 * np.pi * 2000 * t_hi)            # 真 2 kHz

    gap = silence(0.45)
    y = np.concatenate([fade(seg1), gap, fade(seg2), gap, fade(seg3)])
    write_wav("B1_纯音_6k真身_采样后_2k真身.wav", y)


# ---------------------------------------------------------------- C. 电音
NOTE = {"C4": 261.63, "D4": 293.66, "E4": 329.63,
        "F4": 349.23, "G4": 392.00, "A4": 440.00}
SEQ = ["C4", "C4", "G4", "G4", "A4", "A4", "G4",
       "F4", "F4", "E4", "E4", "D4", "D4", "C4"]
BEAT = 0.32


def melody(fs):
    """在给定采样率上直接合成旋律：等价于把连续的谐波叠加音以 fs 取样"""
    total = sum(BEAT * (2 if i in (6, 13) else 1) for i in range(len(SEQ)))
    y = np.zeros(int(total * fs) + 1)
    pos = 0.0
    for i, name in enumerate(SEQ):
        d = BEAT * (2 if i in (6, 13) else 1)
        t = np.arange(int(d * fs)) / fs
        note = np.zeros_like(t)
        f0 = NOTE[name]
        for k in range(1, 15):
            note += (1.0 / k) * np.sin(2 * np.pi * f0 * k * t + 0.3 * k)
        env = np.exp(-1.6 * t / d) * np.minimum(1.0, t / 0.012)
        a = int(pos * fs)
        y[a:a + len(t)] += note * env
        pos += d
    return y


def demo_electric():
    write_wav("C1_星星_原声.wav", melody(FS))
    write_wav("C2_星星_2.6k采样_电音.wav", to_playback(melody(2600), 2600))
    write_wav("C3_星星_1.6k采样_重电音.wav", to_playback(melody(1600), 1600))


# ---------------------------------------------------------------- 波形包络
def peaks_of(x, nbins=420):
    x = np.asarray(x, dtype=float)
    n = max(1, len(x) // nbins)
    m = max(1, len(x) // n)
    p = np.max(np.abs(x[: m * n]).reshape(m, n), axis=1)
    return [round(float(v), 3) for v in p]


def main():
    demo_sweep()
    demo_pure_tone()
    demo_electric()

    peaks = {}
    for name in sorted(os.listdir(OUT)):
        if name.endswith(".wav"):
            with wave.open(os.path.join(OUT, name), "rb") as w:
                raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2") / 32768.0
            peaks[name] = peaks_of(raw)
    with open(os.path.join(OUT, "peaks.js"), "w", encoding="utf-8") as f:
        f.write("window.AUDIO_PEAKS = ")
        json.dump(peaks, f, ensure_ascii=False)
        f.write(";\n")

    for name in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, name)
        print(f"{name:36s} {os.path.getsize(p) / 1024:8.1f} KB")


if __name__ == "__main__":
    main()
