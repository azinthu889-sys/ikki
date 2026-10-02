"""sfxsync — replays prod job j_948437317aa1 (headtop, 2026-09-30), where every cue stayed on plan
time while the pictures moved. Times are the cut-timeline values from that job's worker log,
vplan and the frame audit (`work/ht_audit`)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import sfxsync as SY
import planner as PL

# plan event → where the plan put it on the cut timeline (worker log / vplan)
CUT = {"tpl003": 1.70, "tpl005": 8.64, "pop030": 14.80, "tpl008": 16.22, "fil018": 20.40,
       "tpl011": 24.48, "tpl013": 33.12, "pop031": 33.10, "tpl015": 40.80,
       "fil019": 52.30, "pop032": 52.30, "fil020": 60.72}
KIND = {"tpl003": "hook", "tpl005": "number", "pop030": "pop", "tpl008": "number",
        "fil018": "card", "tpl011": "number", "tpl013": "card", "pop031": "pop",
        "tpl015": "warning", "fil019": "card", "pop032": "pop", "fil020": "card"}
EVENTS = [dict(id=k, startTime=100 + v, endTime=103 + v, style=dict(kind=KIND[k]))
          for k, v in CUT.items()]
BY_SRC = {100 + v: v for v in CUT.values()}


def omap(t, snap=True):
    return BY_SRC.get(round(t, 2))


def _setup():
    SY.reset()
    # full-frame cards respread by _fit_slides (frame audit: 0.0 / 31.1 / 62.0 s)
    SY.set_cards([("p00.mov", 1.70, 7.5, "s"), ("p01.mov", 24.48, 30.1, "s"),
                  ("p02.mov", 40.80, 46.6, "s")],
                 [("p00.mov", 0.00, 4.7, "s"), ("p01.mov", 31.10, 35.7, "s"),
                  ("p02.mov", 62.00, 66.7, "s")])
    # slide-clash step (log: 33.1 → 36.0, 60.7 → 57.8); 20.4 was never built (coverage drop)
    SY.note_move(33.12, 36.00)
    SY.note_move(60.72, 57.80)
    gmov = [(8.64, "a", 3.6), (16.22, "b", 2.9), (36.00, "c", 2.6), (52.30, "d", 2.6),
            (57.80, "e", 2.6)]
    pmov = [(14.80, "x"), (33.10, "y"), (52.30, "z")]
    return gmov, pmov


def test_events_follow_pictures():
    gmov, pmov = _setup()
    out, st = SY.final_events(EVENTS, omap, gmov, pmov)
    at = {e["id"]: e["startTime"] for e in out}
    assert "fil018" not in at, "dropped graphic must lose its sound"
    assert at["tpl003"] == 0.00 and at["tpl011"] == 31.10 and at["tpl015"] == 62.00
    assert at["tpl013"] == 36.00 and at["fil020"] == 57.80
    assert at["tpl005"] == 8.64 and at["pop031"] == 33.10
    assert st["unrendered"] == 1 and st["kept"] == 11


def test_pop_and_card_at_same_time_both_kept():
    gmov, pmov = _setup()
    out, _ = SY.final_events(EVENTS, omap, gmov, pmov)
    ids = {e["id"] for e in out}
    assert {"fil019", "pop032"} <= ids          # side graphic + pop share 52.3 s


def test_unmatched_when_nothing_rendered():
    SY.reset()
    out, st = SY.final_events(EVENTS, omap, [], [])
    assert out == [] and st["unrendered"] == len(EVENTS)


def test_check_catches_the_old_cues_and_passes_the_new():
    gmov, pmov = _setup()
    vis = [0.0, 8.64, 14.8, 16.22, 31.1, 33.1, 36.0, 52.3, 57.8, 62.0]   # rendered starts (incl. pops)
    old = [(2.15, "latch", -17), (8.73, "swipe", -16), (9.09, "click", -18),
           (16.31, "swipe", -16), (16.67, "click", -18), (20.49, "whoosh_in", -15),
           (20.85, "latch", -17), (24.57, "swipe", -16), (24.93, "click", -18),
           (33.21, "whoosh_in", -22), (33.57, "latch", -17), (40.87, "whoosh_in", -21)]
    ok, tot, orph = SY.check(old, vis)
    assert set(round(o, 2) for o in orph) >= {2.15, 20.49, 24.57, 40.87}
    out, _ = SY.final_events(EVENTS, omap, gmov, pmov)
    sfx = PL.sfx_plan(out, 67.5, 8.7, style="headtop", out_dur=67.5)
    new = [(float(e["startTime"]), e["props"]["role"], -16) for e in sfx]
    ok2, tot2, orph2 = SY.check(new, vis)
    assert orph2 == [] and tot2 > 0, orph2


def test_check_in_span_rules():
    vis = [(31.1, 35.7)]
    assert SY.check([(33.21, "whoosh_in", -22)], vis)[2] == [33.21]      # silent entrance
    ok, tot, orph = SY.check([(31.2, "swipe", -16), (32.3, "click", -18)], vis)
    assert orph == [] and tot == 2                                          # in-card follow-up
    assert SY.check([(40.0, "pop", -18)], vis)[2] == [40.0]                 # outside any span


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
