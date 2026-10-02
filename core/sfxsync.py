"""SFX follow the picture — re-anchor plan sound events to where each graphic finally renders.

Why (audit of prod job j_948437317aa1, 2026-10-02): `planner.sfx_plan` derives every cue from
`templateEvents` (plan time). Later stages then move the pictures — `_fit_slides` respreads
full-frame cards for coverage (24.5 → 31.1 s, 40.8 → 62.0 s), the slide-clash step moves side
graphics (33.1 → 36.0, 60.7 → 57.8) or drops them, and the coverage cap drops whole graphics —
but the cues stay on plan time. Result: whooshes over B-roll, a card entering in silence, and a
whoosh+latch over an empty frame. QC only checks that cues are audible, so all of it shipped green.

The worker notes each move here; `final_events()` rebuilds `templateEvents` on the cut timeline
from what actually rendered, so `planner.sfx_plan` (unchanged role/budget logic) runs on the truth.

All times are on the cut (output) timeline.
"""

TOL = 0.60          # an event's mapped start vs a visual's origin — same graphic if within this

_moves = {}         # side graphic: origin at → final at   (slide-clash step)
_drops = set()      # side graphic origins removed after build
_cards = []         # full-frame cards: [(origin at, final at, final end)] after `_fit_slides`


def reset():
    _moves.clear(); _drops.clear(); del _cards[:]


def note_move(origin, final):
    _moves[round(float(origin), 2)] = round(float(final), 2)


def note_drop(origin):
    _drops.add(round(float(origin), 2))


def set_cards(before, after):
    """`before`/`after` — `_fit_slides` input/output `[(path, at, end, layout)]`; paired by path."""
    org = {str(p): float(a) for p, a, _e, _l in (before or [])}
    del _cards[:]
    for p, a, e, _l in (after or []):
        if str(p) in org:
            _cards.append((org[str(p)], float(a), float(e)))


def _side_visuals(gmov):
    """final side graphics `[(origin, final)]` — `gmov` tuples start with the final `at`."""
    inv = {v: k for k, v in _moves.items()}
    out = []
    for g in gmov or []:
        f = round(float(g[0]), 2)
        out.append((inv.get(f, f), f))
    return out


def _nearest(t, pool, used):
    best = None
    for i, (o, f) in enumerate(pool):
        if i in used:
            continue
        d = abs(o - t)
        if d <= TOL and (best is None or d < best[0]):
            best = (d, i, f)
    return best


def final_events(events, omap, gmov=(), pmov=(), log=None):
    """plan `templateEvents` → the same events moved to where they rendered (cut time).

    `omap(t, snap=True)` maps a plan (source) time to the cut timeline, as the worker uses it.
    Events with no rendered picture are left out — their sound must not play.
    Returns `(events, stats)`.
    """
    side = _side_visuals(gmov)
    cards = [(o, f) for o, f, _e in _cards]
    pops = [(round(float(p[0]), 2), round(float(p[0]), 2)) for p in (pmov or [])]
    used = {"side": set(), "card": set(), "pop": set()}
    out, st = [], dict(kept=0, moved=0, unrendered=0, shifts=[])
    for e in sorted(events or [], key=lambda x: x.get("startTime") or 0):
        try:
            t = omap(float(e.get("startTime") or 0.0), snap=True)
        except TypeError:
            t = omap(float(e.get("startTime") or 0.0))
        if t is None:
            st["unrendered"] += 1
            continue
        kind = (e.get("style") or {}).get("kind")
        if kind == "pop":
            cands = [("pop", pops)]
        else:
            cands = [("card", cards), ("side", side)]
        hit = None
        for name, pool in cands:
            h = _nearest(float(t), pool, used[name])
            if h and (hit is None or h[0] < hit[0][0]):
                hit = (h, name)
        if hit is None:
            st["unrendered"] += 1
            continue
        (_d, idx, fin), name = hit
        used[name].add(idx)
        dur = max(0.2, float(e.get("endTime") or 0) - float(e.get("startTime") or 0))
        ne = dict(e); ne["startTime"] = round(fin, 2); ne["endTime"] = round(fin + dur, 2)
        out.append(ne)
        st["kept"] += 1
        if abs(fin - float(t)) > 0.05:
            st["moved"] += 1; st["shifts"].append(round(fin - float(t), 2))
    if log:
        log(f"  🔊 SFX ↔ ရုပ် ပြန်ချိတ် · ဖြစ်ရပ် {len(events or [])} ⇒ တကယ် ပေါ်သော "
            f"{st['kept']} (ရွှေ့ {st['moved']}"
            + (f" · {', '.join(f'{s:+.1f}s' for s in st['shifts'][:6])}" if st['shifts'] else "")
            + f") · ရုပ်မပေါ်၍ အသံဖယ် {st['unrendered']}")
    return out, st


def check(cues, visuals, lead=0.35, lag=0.80):
    """sound↔picture QC — every sound moment must belong to a rendered visual.

    `cues` `[(t, role, db)]` · `visuals` `[(start, end)]` (cut time; a bare number = start only).
    A moment (cues ≤0.4 s apart count once) is synced if it starts within
    `[start − lead, start + lag]` of a visual. Later moments inside a visual's span are allowed
    only if that visual's entrance itself had a sound (motionkit's in-card cues); a sound inside
    a span whose entrance was silent is the drift this module exists to stop.
    Returns `(ok_moments, total, orphans[t])`.
    """
    mom, last = [], None
    for t, _r, _d in sorted(cues or [], key=lambda c: c[0]):
        if last is None or t - last > 0.40:
            mom.append(float(t))
        last = float(t)
    vis = []
    for v in visuals or []:
        a, b = (float(v), float(v)) if isinstance(v, (int, float)) else (float(v[0]), float(v[1]))
        vis.append((a, max(a, b)))
    entered = set()
    orphans = []
    for m in mom:
        hit = [i for i, (a, _b) in enumerate(vis) if a - lead <= m <= a + lag]
        if hit:
            entered.update(hit); continue
        if any(i in entered and a <= m <= b for i, (a, b) in enumerate(vis)):
            continue
        orphans.append(m)
    return len(mom) - len(orphans), len(mom), orphans
