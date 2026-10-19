# -*- coding: utf-8 -*-
r"""
生成全部图片（存到 img/）：

  fig1_四种映射_LHP去哪了.png      四种 s→z 映射：模拟稳定区被搬到哪
  fig2_频率轴畸变与预扭曲.png      三条频率轴映射曲线 + 预扭曲到底救了什么
  fig3_谐波折叠_电音从哪来.png     等间距谐波 → 折叠后不再等间距
  fig4_时频谱_旋律_原声vs电音.png   旋律的时频谱对比
  fig5_时频谱_扫频折叠.png         扫频：一条直线上行，还是上行后折返
  fig6_抗混叠低通响应.png          A3 里那只 FIR 低通的幅频/相频
  fig7_双线性vs脉冲响应不变.png     同一模拟原型，两种数字滤波器的频谱对比
  audio/*.png                      每个 wav 的「波形 + 时频谱」卡片

用法： python py\make_figs.py
"""
import os
import wave

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.normpath(os.path.join(HERE, "..", "img"))
AUD = os.path.normpath(os.path.join(HERE, "..", "audio"))
os.makedirs(os.path.join(IMG, "audio"), exist_ok=True)

plt.rcParams.update({
    "font.family": "Microsoft YaHei",
    "axes.unicode_minus": False,
    "figure.dpi": 120,
    "savefig.dpi": 165,
    "axes.edgecolor": "#555555",
    "axes.labelcolor": "#222222",
    "text.color": "#1a1a1a",
    "axes.grid": True,
    "grid.alpha": 0.22,
    "grid.linestyle": ":",
})

GREEN = "#2f9e6b"
RED = "#d1495b"
BLUE = "#2b5d8c"
ORANGE = "#e07b39"
PURPLE = "#7b5ea7"


def load_wav(name, folder=AUD):
    with wave.open(os.path.join(folder, name), "rb") as w:
        fs = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2") / 32768.0
    return x, fs


def stft_db(x, fs, n=1024, hop=256):
    w = np.hanning(n)
    frames = max(1, (len(x) - n) // hop + 1)
    idx = np.arange(n)[None, :] + hop * np.arange(frames)[:, None]
    seg = x[idx] * w
    S = np.abs(np.fft.rfft(seg, axis=1)).T / (np.sum(w) / 2.0)   # 满幅正弦 = 0 dB
    return 20 * np.log10(S + 1e-9), np.fft.rfftfreq(n, 1 / fs), hop


def save(fig, name):
    p = os.path.join(IMG, name)
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


# ============================================================ 图 1：四种映射
def fig_maps():
    T = 1.0
    sig = np.linspace(-3.0, 1.0, 25)
    omg = np.linspace(-3.2, 3.2, 33)
    SIG, OMG = np.meshgrid(sig, omg)
    S = SIG + 1j * OMG

    maps = [
        ("脉冲响应不变  $z=e^{sT}$", lambda s: np.exp(s * T),
         "σ<0 → |z|=e^{σT}<1  √ 稳定\n但 jω 轴一圈圈绕在单位圆上 → 混叠", 1.75),
        ("前向差分  $z=1+sT$", lambda s: 1 + s * T,
         "σ<0 也会跑到圆外  × 可能不稳定\n（教科书里「不能用」的是这个）", 3.7),
        ("后向差分  $z=1/(1-sT)$", lambda s: 1 / (1 - s * T),
         "√ 稳定，但稳定区只塞进 |z−1/2|<1/2 的小圆\n大 ω 全挤在 z=1 附近 → 高频表示不出来", 1.35),
        ("双线性  $z=\\frac{1+sT/2}{1-sT/2}$", lambda s: (1 + s * T / 2) / (1 - s * T / 2),
         "√ 稳定区恰好填满单位圆（一一对应）\njω 轴 → 单位圆，不重叠 → 不混叠", 1.75),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(11.6, 10.6))
    for ax, (title, f, verdict, lim) in zip(axes.ravel(), maps):
        with np.errstate(divide="ignore", invalid="ignore"):
            Z = f(S)
        ok = np.isfinite(Z)
        Z, sg = Z[ok], SIG[ok]

        ax.add_patch(Circle((0, 0), 1, fill=False, ec="#000000", ls="--", lw=1.2, alpha=0.75))
        stab = sg < 0
        ax.scatter(Z[stab].real, Z[stab].imag, s=10, c=GREEN, alpha=0.55, lw=0, label="来自 σ<0（模拟稳定）")
        ax.scatter(Z[~stab].real, Z[~stab].imag, s=10, c=RED, alpha=0.35, lw=0, label="来自 σ≥0（模拟不稳定）")

        w = np.linspace(-3.2, 3.2, 600)
        Zb = f(1j * w)
        ax.plot(Zb.real, Zb.imag, color=BLUE, lw=2.2, alpha=0.95, label="jω 轴的去向")

        z0 = f(-0.4 + 1.2j)
        ax.plot(z0.real, z0.imag, marker="*", ms=17, color="#111111", zorder=5)
        ax.plot(0, 0, marker="+", ms=9, color="#555555")

        ax.axhline(0, color="#888888", lw=0.8)
        ax.axvline(0, color="#888888", lw=0.8)
        ax.set_aspect("equal")
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)

        frac_bad = np.mean(np.abs(Z[stab]) > 1.0 + 1e-9)
        ax.set_title(title, fontsize=12.5, pad=8)
        ax.text(0.03, 0.03, verdict, transform=ax.transAxes, fontsize=9.4,
                va="bottom", ha="left", linespacing=1.5,
                bbox=dict(boxstyle="round,pad=0.45", fc="#fdf6e3", ec="#d9c58a", alpha=0.95))
        ax.text(0.97, 0.97, f"稳定点越界 {frac_bad * 100:.0f}%", transform=ax.transAxes,
                fontsize=9, ha="right", va="top", color=(RED if frac_bad > 0 else GREEN))
        ax.set_xlabel("Re")
        ax.set_ylabel("Im")

    axes[0, 0].legend(loc="upper left", fontsize=7.8, framealpha=0.92)
    fig.suptitle("把模拟左半平面（稳定区）搬到 z 平面：谁搬丢了，谁搬歪了", fontsize=15, y=0.985)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    return save(fig, "fig1_四种映射_LHP去哪了.png")


# ============================================================ 图 2：频率畸变 + 预扭曲
def butter_poles(n, wc):
    k = np.arange(n)
    return wc * np.exp(1j * np.pi * (2 * k + n + 1) / (2 * n))


def analog_H(w, n, wc):
    p = butter_poles(n, wc)
    return (wc ** n) / np.prod(1j * np.asarray(w)[:, None] - p[None, :], axis=1)


def design(Op, Os, Ap, As, prewarp=True, T=1.0):
    if prewarp:
        wp, ws = 2 / T * np.tan(Op / 2), 2 / T * np.tan(Os / 2)
    else:
        wp, ws = Op, Os
    n = int(np.ceil(np.log10((10 ** (As / 10) - 1) / (10 ** (Ap / 10) - 1))
                    / (2 * np.log10(ws / wp))))
    wc = wp / (10 ** (Ap / 10) - 1) ** (1 / (2 * n))
    return n, wc


def digital_db(Om, n, wc, T=1.0):
    w = 2 / T * np.tan(Om / 2)
    return 20 * np.log10(np.abs(analog_H(w, n, wc)) + 1e-14)


def fig_warp():
    fig = plt.figure(figsize=(15.5, 5.2))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1, 1])

    ax = fig.add_subplot(gs[0, 0])
    Om = np.linspace(1e-4, np.pi, 900)
    ax.plot(Om / np.pi, np.clip(2 * np.tan(Om / 2), 0, 7), color=BLUE, lw=2.4,
            label="双线性  $\\omega T=2\\tan(\\Omega/2)$")
    ax.plot(Om / np.pi, Om, color=GREEN, lw=2.0, ls="--", label="脉冲响应不变  $\\omega T=\\Omega$")
    ax.plot(Om / np.pi, np.sin(Om), color=ORANGE, lw=2.0, ls="-.",
            label="差分法（虚部）  $\\omega T=\\sin\\Omega$")
    ax.axhline(np.pi, color="#999999", lw=0.9, ls=":")
    ax.text(0.02, np.pi + 0.16, "$\\omega T=\\pi$", fontsize=9, color="#666666")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 6.6)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
    ax.set_xticklabels(["0", "0.25π", "0.5π", "0.75π", "π"])
    ax.set_xlabel("数字频率 $\\Omega$")
    ax.set_ylabel("等效模拟频率 $\\omega T$")
    ax.set_title("(a) 频率轴被「压扁」的样子", fontsize=11.5)
    ax.legend(fontsize=8.4, loc="upper left")
    ax.annotate("双线性：越靠近 π 压得越狠\n$\\Omega\\to\\pi$ 时 $\\omega\\to\\infty$", xy=(0.90, 5.0),
                xytext=(0.24, 3.5), fontsize=8.8, color=BLUE,
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.1))
    ax.annotate("差分法：主频到 π/2 就掉头\n→ 高频整个失真", xy=(0.62, 0.8),
                xytext=(0.03, 1.9), fontsize=8.8, color=ORANGE,
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.1))

    cases = [
        (0.20 * np.pi, 0.35 * np.pi, "(b) 低频指标 Ωp=0.2π：忘了预扭曲，通带只差 0.6 dB"),
        (0.42 * np.pi, 0.55 * np.pi, "(c) 高频指标 Ωp=0.42π：忘了预扭曲，通带被砍掉 16 dB"),
    ]
    Ap, As = 1.0, 30.0
    for i, (Op, Os, title) in enumerate(cases):
        ax = fig.add_subplot(gs[0, i + 1])
        n1, wc1 = design(Op, Os, Ap, As, prewarp=True)
        n2, wc2 = design(Op, Os, Ap, As, prewarp=False)

        Og = np.linspace(1e-3, 0.72 * np.pi, 1600)
        d1 = digital_db(Og, n1, wc1)
        d2 = digital_db(Og, n2, wc2)

        a1p = np.interp(Op, Og, d1)
        a1s = np.interp(Os, Og, d1)
        a2p = np.interp(Op, Og, d2)
        a2s = np.interp(Os, Og, d2)

        ax.plot(Og / np.pi, d1, color=GREEN, lw=2.2,
                label=f"预扭曲后设计 n={n1}：Ωp {a1p:.1f} dB，Ωs {a1s:.0f} dB")
        ax.plot(Og / np.pi, d2, color=RED, lw=2.0, ls="--",
                label=f"忘预扭曲 n={n2}：Ωp {a2p:.1f} dB，Ωs {a2s:.0f} dB")
        ax.axvline(Op / np.pi, color="#333333", lw=1.0, ls=":")
        ax.axvline(Os / np.pi, color="#333333", lw=1.0, ls=":")
        ax.axhline(-Ap, color=ORANGE, lw=0.9, ls=":")
        ax.axhline(-As, color=ORANGE, lw=0.9, ls=":")
        ax.text(Op / np.pi, 2, "Ωp", fontsize=9, ha="center")
        ax.text(Os / np.pi, 2, "Ωs", fontsize=9, ha="center")
        ax.text(0.015, -Ap + 1.5, f"−{Ap:.0f} dB", fontsize=8.5, color=ORANGE)
        ax.text(0.015, -As + 1.5, f"−{As:.0f} dB", fontsize=8.5, color=ORANGE)

        ax.set_xlim(0, 0.72)
        ax.set_ylim(-55, 6)
        ax.set_xlabel("数字频率 $\\Omega$ (×π)")
        ax.set_ylabel("$|H(e^{j\\Omega})|$ / dB")
        ax.set_title(title, fontsize=11)
        ax.legend(fontsize=8.0, loc="lower left", framealpha=0.95)

    fig.suptitle("频率畸变长什么样，预扭曲补的是哪一段", fontsize=15, y=1.0)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return save(fig, "fig2_频率轴畸变与预扭曲.png")


# ============================================================ 图 3：谐波折叠
def fig_fold():
    f0, fs = 261.63, 2600.0
    k = np.arange(1, 15)
    f = k * f0
    amp = 1.0 / k
    alias = np.abs(((f + fs / 2) % fs) - fs / 2)
    folded = f > fs / 2

    fig, axes = plt.subplots(2, 1, figsize=(10.6, 7.6))

    ax = axes[0]
    ax.vlines(f[~folded], 0, amp[~folded], color=GREEN, lw=2.2, label="低于 Nyquist，原样通过")
    ax.vlines(f[folded], 0, amp[folded], color=ORANGE, lw=2.2, label="高于 Nyquist，会被折叠")
    ax.axvline(fs / 2, color=RED, ls="--", lw=1.4)
    ax.text(fs / 2 + 40, 0.86, "Nyquist = 1300 Hz", color=RED, fontsize=9.5)
    ax.set_xlim(0, 3900)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("频率 / Hz")
    ax.set_ylabel("谐波幅度")
    ax.set_title("采样前：C4 的谐波严格等间距（间距 = 基频 262 Hz）", fontsize=11.5)
    ax.legend(fontsize=9, loc="upper right")

    ax = axes[1]
    for g in np.arange(1, 6) * f0:
        ax.axvline(g, color="#bbbbbb", ls=":", lw=1.1)
    ax.vlines(alias[~folded], 0, amp[~folded], color=GREEN, lw=2.2, label="原样通过（仍落在 k·f0 上）")
    ax.vlines(alias[folded], 0, amp[folded], color=ORANGE, lw=2.2, label="折叠后的新分音（不落在 k·f0 上）")
    ax.set_xlim(0, 1400)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("频率 / Hz")
    ax.set_ylabel("谐波幅度")
    ax.set_title("2.6 kHz 采样之后：折叠出来的分音「插」在谐波之间 → 不再是谐波列", fontsize=11.5)
    ax.legend(fontsize=9, loc="upper right")

    fig.suptitle("混叠为什么听起来像「电音」：等间距谐波被折叠成不等间距", fontsize=14.5, y=1.0)
    fig.text(0.5, 0.015,
             "灰点线 = 原来的 k·f0 位置　橙线 = 折叠后的实际频率　"
             "耳朵判断「乐音」靠谐波成整数倍；间距被打乱 → 金属感、走音感，就是你说的「电音」",
             ha="center", fontsize=9.4,
             bbox=dict(boxstyle="round,pad=0.5", fc="#fdf6e3", ec="#d9c58a"))
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    return save(fig, "fig3_谐波折叠_电音从哪来.png")


# ============================================================ 图 4：旋律时频谱
def fig_spec_melody():
    fig, axes = plt.subplots(2, 1, figsize=(11.2, 7.2), sharex=True)
    for ax, name, fmax, title in [
        (axes[0], "C1_星星_原声.wav", 4000, "原声：谐波是一条条水平线，间距均匀（=基频）"),
        (axes[1], "C2_星星_2.6k采样_电音.wav", 1300, "2.6 kHz 采样后：谱线被打乱，还冒出原本没有的横线"),
    ]:
        x, fs = load_wav(name)
        S, freqs, hop = stft_db(x, fs)
        t = np.arange(S.shape[1]) * hop / fs
        ax.imshow(S, origin="lower", aspect="auto", cmap="magma", interpolation="nearest",
                  extent=[t[0], t[-1], freqs[0], freqs[-1]], vmin=-90, vmax=-5)
        ax.set_ylim(0, fmax)
        ax.set_ylabel("频率 / Hz")
        ax.set_title(title, fontsize=11.5)
        ax.grid(False)
    axes[1].set_xlabel("时间 / s")
    fig.suptitle("时频谱：一小列一小列是音符，横线是谐波", fontsize=14, y=1.0)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return save(fig, "fig4_时频谱_旋律_原声vs电音.png")


# ============================================================ 图 5：扫频折叠
def fig_spec_sweep():
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    t0 = 0
    for ax, name, title in [
        (axes[0], "A1_扫频_原声.wav", "原声（44.1 kHz）：一条笔直上行的斜线"),
        (axes[1], "A2_扫频_8k采样_无抗混叠.wav", "8 kHz 采样：过 4 kHz 后「折返」下行"),
    ]:
        x, fs = load_wav(name)
        S, freqs, hop = stft_db(x, fs, n=2048, hop=256)
        t = np.arange(S.shape[1]) * hop / fs
        ax.imshow(S, origin="lower", aspect="auto", cmap="magma", interpolation="nearest",
                  extent=[t[0], t[-1], freqs[0], freqs[-1]], vmin=-90, vmax=-5)
        tt = np.linspace(0, 6, 800)
        f_inst = 200 + 7400 * tt / 6
        ax.plot(tt, f_inst, color="#7ef7c8", lw=1.4, ls="--", alpha=0.9, label="理论瞬时频率")
        if "A2" in name:
            folded = np.where(f_inst < 4000, f_inst, 8000 - f_inst)
            ax.plot(tt, folded, color="#ffd166", lw=1.8, alpha=0.95, label="折叠后的实际频率")
        ax.axhline(4000, color="#dddddd", lw=0.9, ls=":", alpha=0.75)
        ax.set_ylim(0, 8000)
        ax.set_xlabel("时间 / s")
        ax.set_title(title, fontsize=11.5)
        ax.grid(False)
        ax.legend(fontsize=8.5, loc="upper left")
        ax.text(0.02, 3980, "4 kHz = 8 kHz 的 Nyquist", color="w", fontsize=8.5, va="top")
    axes[0].set_ylabel("频率 / Hz")
    fig.suptitle("「折返」在时频谱上就是这样一条镜像线", fontsize=14, y=1.0)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return save(fig, "fig5_时频谱_扫频折叠.png")


# ============================================================ 图 6：抗混叠 FIR 响应
def fig_aa_filter():
    from scipy.signal import firwin, freqz

    fs = 44100
    h = firwin(1023, 3400, fs=fs, window=("kaiser", 8.0))
    w, H = freqz(h, worN=8192, fs=fs)
    db = 20 * np.log10(np.abs(H) + 1e-12)

    fig, axes = plt.subplots(2, 1, figsize=(10.6, 6.2), sharex=True,
                             gridspec_kw={"height_ratios": [2.3, 1]})
    ax = axes[0]
    ax.plot(w, db, color=BLUE, lw=1.8)
    ax.axvline(3400, color=GREEN, ls="--", lw=1.3)
    ax.axvline(4000, color=RED, ls="--", lw=1.3)
    ax.text(3380, -6, "通带边缘 3.4 kHz", color=GREEN, fontsize=9, ha="right")
    ax.text(4060, -26, "阻带起点 4 kHz\n（= 8 kHz 的 Nyquist）", color=RED, fontsize=9)
    ax.set_ylim(-110, 8)
    ax.set_xlim(0, 8000)
    ax.set_ylabel("$|H|$ / dB")
    ax.set_title("A3 用的那只 FIR 低通：1023 阶、Kaiser β=8、阻带深于 −90 dB", fontsize=12)

    ax2 = axes[1]
    ph = np.unwrap(np.angle(H))
    ax2.plot(w, ph, color=PURPLE, lw=1.4)
    ax2.set_xlabel("频率 / Hz")
    ax2.set_ylabel("相位 / rad")
    ax2.set_title("通带内的相位是一条直线 → 线性相位（群延迟恒为 (N−1)/2 = 511 点）", fontsize=10.5)
    ax2.set_xlim(0, 3400)
    fig.tight_layout()
    return save(fig, "fig6_抗混叠低通响应.png")


# ============================================================ 图 7：双线性 vs 脉冲响应不变
def fig_bilinear_vs_imp():
    T = 1.0
    n = 4
    wc_analog = 2 * np.tan(0.15 * np.pi)      # 数字截止 0.3π 预扭曲后的模拟截止
    w = np.linspace(0, np.pi, 2000)

    # 双线性：H_d(Ω) = H_a(j·2tan(Ω/2))
    H_bil = analog_H(2 * np.tan(w / 2), n, wc_analog)

    # 脉冲响应不变：频域混叠求和 H_d(Ω) = (1/T) Σ H_a(j(Ω-2πk)/T)
    H_imp = np.zeros_like(H_bil, dtype=complex)
    for k in range(-25, 26):
        H_imp += analog_H((w - 2 * np.pi * k) / T, n, wc_analog) / T

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})

    ax = axes[0]
    ax.plot(w / np.pi, 20 * np.log10(np.abs(H_bil) + 1e-12), color=GREEN, lw=2.3,
            label="双线性（预扭曲到 0.3π）")
    ax.plot(w / np.pi, 20 * np.log10(np.abs(H_imp) + 1e-12), color=ORANGE, lw=2.0,
            label="脉冲响应不变（同一模拟原型）")
    ax.axvline(0.3, color="#333333", ls=":", lw=1.0)
    ax.text(0.305, 2, "目标截止 0.3π", fontsize=9)
    ax.set_ylim(-100, 8)
    ax.set_xlim(0, 1)
    ax.set_xlabel("数字频率 $\\Omega$ (×π)")
    ax.set_ylabel("$|H|$ / dB")
    ax.set_title("同一只 4 阶 Butterworth 原型，两种映射出来的数字滤波器", fontsize=11.5)
    ax.legend(fontsize=9, loc="lower left")
    ax.text(0.98, 0.95,
            "脉冲响应不变：阻带只压到 −33 dB 就被混叠「托住」了\n"
            "双线性：阻带一路往下走，−80 dB 以下仍然干净",
            transform=ax.transAxes, fontsize=8.8, ha="right", va="top", linespacing=1.5,
            bbox=dict(boxstyle="round,pad=0.4", fc="#fdf6e3", ec="#d9c58a"))

    ax = axes[1]
    ax.add_patch(Circle((0, 0), 1, fill=False, ec="k", ls="--", lw=1.1))
    p_s = butter_poles(n, wc_analog)
    p_bil = (1 + p_s * T / 2) / (1 - p_s * T / 2)
    p_imp = np.exp(p_s * T)
    ax.plot(p_bil.real, p_bil.imag, "o", ms=8, mfc="none", mec=GREEN, mew=1.8, label="双线性映射后的极点")
    ax.plot(p_imp.real, p_imp.imag, "s", ms=7, mfc="none", mec=ORANGE, mew=1.6, label="脉冲响应不变映射后的极点")
    ax.plot(-np.ones(n), np.zeros(n), "x", ms=9, color=PURPLE, mew=1.8,
            label="双线性的零点：全在 z=−1")
    ax.axhline(0, color="#888888", lw=0.8)
    ax.axvline(0, color="#888888", lw=0.8)
    ax.set_aspect("equal")
    ax.set_xlim(-2.4, 1.6)
    ax.set_ylim(-1.3, 1.3)
    ax.set_xlabel("Re")
    ax.set_ylabel("Im")
    ax.set_title("零极点：两种映射都把极点关进单位圆", fontsize=11)
    ax.legend(fontsize=7.8, loc="lower left")

    fig.tight_layout()
    return save(fig, "fig7_双线性vs脉冲响应不变.png")


# ============================================================ 每个 wav 的波形+时频谱卡片
FMAX = {
    "A1_扫频_原声.wav": 8000,
    "A2_扫频_8k采样_无抗混叠.wav": 8000,
    "A3_扫频_先低通再8k采样.wav": 4000,
    "B1_纯音_6k真身_采样后_2k真身.wav": 8000,
    "C1_星星_原声.wav": 4000,
    "C2_星星_2.6k采样_电音.wav": 1300,
    "C3_星星_1.6k采样_重电音.wav": 800,
}
NOTE = {
    "A1_扫频_原声.wav": "44.1 kHz 直接合成，200→7600 Hz 一路上去，什么也没发生。",
    "A2_扫频_8k采样_无抗混叠.wav": "按 8 kHz 取样：4 kHz 以上全部折返，所以后半段是「镜像」往下走。",
    "A3_扫频_先低通再8k采样.wav": "先过 3.4 kHz 低通再取样：3.4 kHz 以上被掐掉，谱图上直接空白，没有折返。",
    "B1_纯音_6k真身_采样后_2k真身.wav": "① 6 kHz ② 6 kHz 经 8 kHz 采样 ③ 真 2 kHz —— ② 和 ③ 的谱完全重合。",
    "C1_星星_原声.wav": "谐波列整齐，听起来是「乐器」。",
    "C2_星星_2.6k采样_电音.wav": "1.3 kHz 以上谐波折叠，插进谐波之间 → 金属感。",
    "C3_星星_1.6k采样_重电音.wav": "Nyquist 只剩 800 Hz，连 3 次谐波都保不住 → 8-bit 破碎感。",
}


def audio_cards():
    out = []
    for name, fmax in FMAX.items():
        x, fs = load_wav(name)
        t = np.arange(len(x)) / fs
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.4, 3.1), sharex=True,
                                       gridspec_kw={"height_ratios": [1, 2.4]})
        # 波形包络（抽样画，避免几十万点）
        nb = 1600
        edges = np.linspace(0, len(x), nb + 1).astype(int)
        tt, lo, hi = [], [], []
        for a, b in zip(edges[:-1], edges[1:]):
            if b > a:
                seg = x[a:b]
                tt.append((a + b) / 2 / fs)
                lo.append(seg.min())
                hi.append(seg.max())
        ax1.fill_between(tt, lo, hi, color=BLUE, lw=0, alpha=0.85)
        ax1.set_ylim(-1.05, 1.05)
        ax1.set_yticks([-1, 0, 1])
        ax1.set_ylabel("波形")

        S, freqs, hop = stft_db(x, fs)
        tS = np.arange(S.shape[1]) * hop / fs
        ax2.imshow(S, origin="lower", aspect="auto", cmap="magma", interpolation="nearest",
                   extent=[tS[0], tS[-1], freqs[0], freqs[-1]], vmin=-90, vmax=-5)
        ax2.set_ylim(0, fmax)
        ax2.set_ylabel("频率 / Hz", fontsize=9.5)
        ax2.set_xlabel("时间 / s", fontsize=9.5)
        ax2.tick_params(labelsize=8.5)
        ax2.grid(False)
        ax1.tick_params(labelsize=8.5)
        ax1.set_ylabel("波形", fontsize=9.5)
        ax1.grid(False)
        fig.tight_layout()
        p = os.path.join(IMG, "audio", name.replace(".wav", ".png"))
        fig.savefig(p, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        out.append(p)
    return out


if __name__ == "__main__":
    for f in (fig_maps, fig_warp, fig_fold, fig_spec_melody, fig_spec_sweep,
              fig_aa_filter, fig_bilinear_vs_imp):
        print("done:", os.path.basename(f()))
    print("cards:", len(audio_cards()))
