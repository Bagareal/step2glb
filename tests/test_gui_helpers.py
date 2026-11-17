from step2glb.__main__ import clean_argv
from step2glb.gui import STATUS_TEXT, format_elapsed, format_size, phase_text


def test_format_size():
    assert format_size(0) == "0 B"
    assert format_size(512) == "512 B"
    assert format_size(1536) == "1.5 KB"
    assert format_size(204800) == "200 KB"
    assert format_size(12 * 1024 ** 2) == "12 MB"


def test_clean_argv_drops_macos_process_serial():
    assert clean_argv(["-psn_0_12345", "a.step"]) == ["a.step"]
    assert clean_argv(["-q", "draft", "a.step"]) == ["-q", "draft", "a.step"]


def test_status_text_covers_all_states():
    assert set(STATUS_TEXT) == {"queued", "running", "done", "error", "cancelled"}


def test_phase_text_shows_percent_only_when_known():
    assert phase_text("read", None) == "Reading file…"
    assert phase_text("transfer", None) == "Building shapes…"
    assert phase_text("mesh", None) == "Meshing…"
    assert phase_text("mesh", 0.456) == "Meshing 45%"
    assert phase_text("write", 1.0) == "Writing GLB…"


def test_format_elapsed():
    assert format_elapsed(0) == "0:00"
    assert format_elapsed(75.9) == "1:15"
    assert format_elapsed(3725) == "1:02:05"
