"""Planner props are passed to MotionKit builders without losing their values."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

import dress as DR  # noqa: E402


FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name} {detail}")


def main():
    def tagged(tag, title, dur=None):
        return tag, title, dur

    def plain(text, dur=None):
        return text, dur

    # Avoid catalog imports in this focused unit test; the call mechanics are
    # what caused dict keys to be rendered as positional values.
    old = dict(DR._TAGQ)
    try:
        DR._TAGQ.update({"brows.window_open": True, "callouts.box_call": False})
        got = DR._call_template(tagged, "brows.window_open", "g0",
                                {"title": "IKKI app", "dur": 2.4})
        check("tagged template က dict props ကို keyword နဲ့ရသည်",
              got == ("g0", "IKKI app", 2.4), got)
        got2 = DR._call_template(plain, "callouts.box_call", "g1",
                                 {"text": "အရေးကြီး", "dur": 1.8})
        check("tag မလို template က dict props ကို keyword နဲ့ရသည်",
              got2 == ("အရေးကြီး", 1.8), got2)
        got3 = DR._call_template(tagged, "brows.window_open", "g2",
                                 ("Title", 1.2))
        check("legacy positional recipe မပျက်", got3 == ("g2", "Title", 1.2), got3)
    finally:
        DR._TAGQ.clear(); DR._TAGQ.update(old)
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
