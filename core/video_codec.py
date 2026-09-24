#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portable H.264 encoder arguments for every IKKI render stage.

The creator Mac can use VideoToolbox, but the production worker is Linux and
does not ship that macOS encoder.  Keeping this choice in one place prevents a
cut-preview succeeding on one machine while the final overlay or B-roll pass
silently selects an unavailable encoder on another.
"""
import os
import platform


def preferred_codec():
    """Return an explicit override, otherwise the native safe H.264 encoder."""
    override = (os.environ.get("IKKI_VCODEC") or "").strip()
    if override:
        return override
    return "h264_videotoolbox" if platform.system() == "Darwin" else "libx264"


def h264_args(bitrate=None, *, crf=18, preset=None):
    """Return ffmpeg arguments for a premium, browser-compatible H.264 file.

    ``-b:v`` is retained for Apple's hardware encoder.  Linux uses libx264 in
    CRF mode so source detail is not capped by a bitrate chosen for a different
    resolution.  ``veryfast`` is deliberate on the 1.8-vCPU worker; it is a
    speed setting, while CRF 18 is the quality control.
    """
    codec = preferred_codec()
    args = ["-c:v", codec]
    if codec == "libx264":
        quality = max(0, min(51, int(round(float(crf)))))
        args += [
            "-preset", preset or os.environ.get("IKKI_X264_PRESET", "veryfast"),
            "-crf", str(quality),
            "-pix_fmt", "yuv420p",
        ]
    elif bitrate:
        args += ["-b:v", str(bitrate)]
    return args
