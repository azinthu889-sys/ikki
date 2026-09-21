"""User-edited text stays intact while its old ASR times are realigned."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))
import asr as A  # noqa: E402


def main():
    # Speech starts after each measured pause. Supplied timestamps are 0.4s early.
    meas = ([(1.0, 2.4), (4.0, 5.3)],
            [(0.0, 1.0), (2.4, 4.0), (5.3, 6.0)], 6.0, {}, "aroll")
    src = [dict(id="a", text="first user edit", start=0.6, end=2.0),
           dict(id="b", fix="second user edit", start=3.6, end=5.0)]
    got = A.align_provided(src, meas, cfg=dict(bias_s=0.0, window_s=1.0))

    assert [x["text"] for x in got] == ["first user edit", "second user edit"]
    assert [x["id"] for x in got] == ["a", "b"]
    assert got[0]["start"] == 1.0 and got[1]["start"] == 4.0, got
    assert all(x["timing_src"].startswith("provided_") for x in got), got
    print("  ✓ provided text is preserved and audio-aligned")


if __name__ == "__main__": 
    main()
