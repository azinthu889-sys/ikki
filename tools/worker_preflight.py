#!/usr/bin/env python3
"""Fail-fast validation for the IKKI render-worker runtime.

Run this inside the worker image after every VPS deployment.  It verifies the
actual tools and mounted libraries used by a render; it deliberately does not
claim that a queue loop is healthy merely because the Python process started.
"""
import os
import shutil
import sys
import tempfile


def fail(message):
    print(f"FAIL  {message}", flush=True)
    return 1


def main():
    linux_text = os.environ.get("MK_TEXT") == "rsvg"
    required_commands = ["ffmpeg", "ffprobe"] + (["rsvg-convert"] if linux_text else [])
    missing = [cmd for cmd in required_commands if not shutil.which(cmd)]
    if missing:
        return fail("system commands missing: " + ", ".join(missing))

    mk = os.environ.get("IKKI_MOTIONKIT", "")
    assets = os.environ.get("IKKI_ASSETS", "")
    if not os.path.isfile(os.path.join(mk, "cttext_rsvg.py")):
        return fail("Motion Kit Linux text fallback is missing")
    if linux_text and os.path.isfile(os.path.join(mk, "cttext")):
        return fail("macOS cttext binary is present in Linux runtime")
    if not os.path.isfile(os.path.join(assets, "broll", "index.json")):
        return fail("curated IKKI assets are not mounted")

    try:
        import numpy  # noqa: F401
        from PIL import Image  # noqa: F401
        import broll as BR
        import gfxcat as GC
        import sfxpool as SP
        import slide as SL
    except Exception as exc:
        return fail(f"Python import: {type(exc).__name__}: {exc}")

    clips = BR.load().get("clips") or []
    if not clips:
        return fail("B-roll index resolves zero usable clips")

    role_counts = SP.stats(ship=True)
    required_roles = ("click", "pop", "swipe", "whoosh", "impact", "riser", "shimmer")
    unavailable = [role for role in required_roles if not role_counts.get(role)]
    if unavailable:
        return fail("licensed SFX pool empty: " + ", ".join(unavailable))

    if not SL.available():
        return fail("neither CoreText nor the Linux text fallback is available")
    try:
        SL.setsize(640, 360)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as out:
            png = out.name
        try:
            SL.statement("IKKI မှာ စာသားစစ်ဆေးခြင်း", brand="IKKI").convert("RGB").save(png)
            if os.path.getsize(png) < 1000:
                return fail("Myanmar slide output is unexpectedly empty")
        finally:
            try:
                os.unlink(png)
            except OSError:
                pass
    except Exception as exc:
        return fail(f"Myanmar slide render: {type(exc).__name__}: {exc}")

    templates = GC.usable()
    if len(templates) < 100:
        return fail(f"Motion Kit template catalog too small: {len(templates)}")

    print(
        "OK    tools=" + ",".join(required_commands) + " "
        f"broll={len(clips)} templates={len(templates)} "
        "sfx=" + ",".join(f"{k}:{role_counts[k]}" for k in required_roles),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
