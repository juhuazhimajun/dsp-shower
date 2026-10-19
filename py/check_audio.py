# -*- coding: utf-8 -*-
r"""
自检脚本：不听声音，用「数主频」证明混叠真的发生了。

对 A1/A2/A3 在几个时刻截 8192 点做 FFT（加 Hann 窗），打印该窗内的主频。
扫频是 200→7600 Hz / 6 s，所以 t 秒时刻的瞬时频率约为
    f(t) = 200 + 7400*t/6  (+115 Hz，因为 Hann 窗中心在窗口正中，约 t+0.093 s)

  A1 原声   : 随 t 单调上升
  A2 未滤波 : 过 4 kHz 后主频「倒着走」（折返）
  A3 先低通 : 3.4 kHz 以上几乎无主频（被掐死）

用法： python py\check_audio.py
"""
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "audio"))
FS = 44100


def load(name):
    with wave.open(os.path.join(OUT, name), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2") / 32768.0


def dom_freq(x, t, n=8192):
    a = int(t * FS)
    seg = x[a:a + n]
    if len(seg) < n:
        return float("nan"), -999.0
    seg = seg * np.hanning(len(seg))
    sp = np.abs(np.fft.rfft(seg))
    k = int(np.argmax(sp))
    db = 20 * np.log10(sp[k] / len(seg) * 4 + 1e-15)
    return k * FS / len(seg), db


def main():
    files = ["A1_扫频_原声.wav", "A2_扫频_8k采样_无抗混叠.wav", "A3_扫频_先低通再8k采样.wav"]
    times = (1, 2, 3, 4, 5)
    print("=" * 84)
    print(f"{'文件':34s}" + "".join(f"t={t}s".rjust(12) for t in times))
    print("-" * 84)
    for name in files:
        x = load(name)
        row = ""
        for t in times:
            f, db = dom_freq(x, t)
            row += f"{f:7.0f}Hz/{db:4.0f}dB".rjust(12)
        print(f"{name[:32]:34s}" + row)
    print("-" * 84)
    print("理论瞬时频率(含窗中心偏移 +115 Hz)： 1548   2782   4015   5250   6482")
    print("8000 Hz 采样后的镜像：  8000-f  →  6452   5218   3985   2750   1518")
    print("→ A2 的 t=4s/5s 主频掉回 2800/1500 Hz，这就是折返；A3 在 t≥4s 只剩静音。")
    print()

    # 电音：把 C4 的谐波和「采样后应该落到哪里」逐条对出来
    f0 = 261.63
    fs = 2600.0
    print(f"C4 谐波 k*f0 与 {fs:.0f} Hz 采样后的落点（折叠公式：|((f+fs/2) mod fs) - fs/2|）")
    for k in range(1, 11):
        f = k * f0
        alias = abs(((f + fs / 2) % fs) - fs / 2)
        flag = "  ← 原样通过" if f < fs / 2 else f"  ← 折叠到 {alias:6.0f} Hz（偏 {abs(alias - f):5.0f} Hz）"
        print(f"  k={k:2d}  {f:7.1f} Hz{flag}")


if __name__ == "__main__":
    main()
