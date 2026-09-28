# -*- coding: utf-8 -*-
"""Acoustic word-onset alignment (short-916 · Zin 2026-09-28: "subtitle timing
must match the voice exactly").

Gemini's word times are ±0.3 s (measured: word start − run start p5 −0.31 /
p95 +0.37). Cards that switch inside a speech run take their time from those
words, so ~3/4 of card switches landed off the syllable. This moves every
word start inside a run onto an acoustic syllable boundary:

  1. syllable count per word from the text (Burmese syllables, Latin vowel groups)
  2. valleys of the voice-band energy envelope inside the run = candidate
     syllable boundaries
  3. dynamic programming picks one valley per word boundary, monotonic, scoring
     closeness to a prior (Gemini time blended with the syllable-proportional
     position) and valley depth.

The first word of a run starts at the run start (acoustic, exact). Words are
never changed, added or reordered -- only their start/end times (R1).
"""
import re
import numpy as np

HOP = 0.01

def syl_count(w):
    w = str(w)
    if re.search(r"[က-႟]", w):
        try:
            import captions as CP
            return max(1, len([s for s in CP.syllables(w) if s.strip()]))
        except Exception:
            return max(1, len(re.findall(r"[က-အ]", w)))
    return max(1, len(re.findall(r"[aeiouy]+", w.lower())))

def envelope(x, sr, lo=300.0, hi=3400.0, hop=HOP, win=0.025):
    """voice-band energy (dB) at `hop` s, lightly smoothed"""
    n = int(win * sr); h = int(hop * sr)
    if len(x) < n: return np.zeros(1)
    fr = np.lib.stride_tricks.sliding_window_view(x, n)[::h]
    S = np.abs(np.fft.rfft(fr * np.hanning(n), axis=1)) ** 2
    f = np.fft.rfftfreq(n, 1 / sr); b = (f >= lo) & (f <= hi)
    e = 10 * np.log10(S[:, b].sum(1) + 1e-10)
    k = np.ones(3) / 3
    return np.convolve(e, k, "same")

def valleys(e, a, b, hop=HOP, min_gap=0.06):
    """(time, depth) of local minima of `e` inside [a, b]"""
    i0, i1 = max(1, int(a / hop)), min(len(e) - 2, int(b / hop))
    out = []
    for i in range(i0, i1):
        if e[i] <= e[i - 1] and e[i] <= e[i + 1]:
            lo, hi = max(0, i - 8), min(len(e), i + 9)
            depth = min(e[lo:i].max(), e[i + 1:hi].max()) - e[i]
            if depth > 0.8:
                if out and i * hop - out[-1][0] < min_gap:
                    if depth > out[-1][1]: out[-1] = (i * hop, depth)
                    continue
                out.append((i * hop, depth))
    return out

def align_run(words, a, b, e, sigma=0.12, alpha=0.5, w_depth=0.04, min_dur=0.06):
    """words: [(w, s, e)] inside run [a, b] -> new start times (list)"""
    m = len(words)
    if m == 0: return []
    if m == 1: return [a]
    c = np.array([syl_count(w[0]) for w in words], float)
    cum = np.cumsum(c)[:-1] / c.sum()
    prior = [alpha * float(words[j + 1][1]) + (1 - alpha) * (a + cum[j] * (b - a)) for j in range(m - 1)]
    V = valleys(e, a + min_dur, b - min_dur)
    if not V: return [a] + [min(b, max(a, p)) for p in prior]
    vt = np.array([v[0] for v in V]); vd = np.array([v[1] for v in V])
    K = len(V); J = m - 1
    INF = 1e18
    # cost[j][k]: best cost with boundary j placed at valley k
    cost = np.full((J, K), INF); back = np.full((J, K), -1, int)
    loc = lambda j, k: ((vt[k] - prior[j]) / sigma) ** 2 - w_depth * vd[k]
    for k in range(K):
        if vt[k] - a >= min_dur: cost[0, k] = loc(0, k)
    for j in range(1, J):
        best = INF; bk = -1; kk = 0
        for k in range(K):
            # predecessor must be at least min_dur earlier
            while kk < K and vt[kk] <= vt[k] - min_dur:
                if cost[j - 1, kk] < best: best, bk = cost[j - 1, kk], kk
                kk += 1
            if bk >= 0: cost[j, k] = best + loc(j, k); back[j, k] = bk
    k = int(np.argmin(cost[J - 1]))
    if cost[J - 1, k] >= INF:                                  # fewer valleys than boundaries
        return [a] + [min(b, max(a, p)) for p in prior]
    ks = [k]
    for j in range(J - 1, 0, -1):
        k = back[j, k]; ks.append(int(k))
    ks.reverse()
    return [a] + [float(vt[k]) for k in ks]

def align(words, runs, x, sr):
    """words [(w, s, e)] (cut timeline) · runs [(a, b)] · x mono audio of the
    cut timeline -> words with refined (s, e). Words outside every run keep
    their times."""
    e = envelope(x, sr)
    W = sorted([(str(w[0]), float(w[1]), float(w[2])) for w in words], key=lambda t: (t[1], t[2]))
    by_run = [[] for _ in runs]; free = []
    for i, w in enumerate(W):
        ov = [max(0.0, min(w[2], b) - max(w[1], a)) for a, b in runs]
        k = int(np.argmax(ov)) if ov and max(ov) > 0 else -1
        (by_run[k] if k >= 0 else free).append(i)
    out = list(W)
    for (a, b), idx in zip(runs, by_run):
        if not idx: continue
        st = align_run([W[i] for i in idx], a, b, e)
        for n, i in enumerate(idx):
            s = st[n]; en = st[n + 1] if n + 1 < len(idx) else b
            out[i] = (W[i][0], round(s, 3), round(max(s + 0.02, en), 3))
    return out
