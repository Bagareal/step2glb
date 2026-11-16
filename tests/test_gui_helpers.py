from step2glb.__main__ import clean_argv
from step2glb.gui import STATUS_TEXT, format_size


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
    assert set(STATUS_TEXT) == {"queued", "running", "done", "error"}
