"""Cards stay near their sentence (Zin 2026-10-02). Replays j_948437317aa1's three plan cards:
without the limit `_fit_slides` respread them to 0 / 31.1 / 62.0 s (KBZPay card 21 s late)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import run as W

CARDS = [("p00.mov", 1.70, 7.50, "s"), ("p01.mov", 24.48, 30.12, "s"), ("p02.mov", 40.80, 46.60, "s")]
DUR = 67.5
LO, HI = 0.17 * DUR, 0.25 * DUR
CMAX = 10.5


def _cov(out):
    return sum(b - a for _p, a, b, _l in out)


def test_old_behaviour_moved_cards_far():
    out, _ = W._fit_slides(list(CARDS), LO, HI, CMAX, dur=DUR)
    far = max(abs(a - dict((p, x) for p, x, _e, _l in CARDS)[p]) for p, a, _b, _l in out)
    print("  without limit:", [(round(a, 1), round(b, 1)) for _p, a, b, _l in out], "max shift", round(far, 1))


def test_cards_stay_near_and_coverage_holds():
    out, why = W._fit_slides(list(CARDS), LO, HI, CMAX, dur=DUR, max_shift=W.CARD_NEAR)
    anc = {p: a for p, a, _e, _l in CARDS}
    shifts = [abs(a - anc[p]) for p, a, _b, _l in out]
    print("  with limit:", [(round(a, 1), round(b, 1)) for _p, a, b, _l in out], why)
    assert len(out) == 3
    assert max(shifts) <= W.CARD_NEAR + 1e-6, shifts
    assert LO - 1e-6 <= _cov(out) <= HI + 1e-6, _cov(out) / DUR


def test_no_limit_is_unchanged():
    a, _ = W._fit_slides(list(CARDS), LO, HI, CMAX, dur=DUR)
    b, _ = W._fit_slides(list(CARDS), LO, HI, CMAX, dur=DUR, max_shift=None)
    assert a == b


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
