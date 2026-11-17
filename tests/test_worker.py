import multiprocessing
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from make_sample import make_sample

from step2glb.converter import Options
from step2glb.worker import run_job


def _run(src, dst):
    ctx = multiprocessing.get_context("spawn")  # what the window uses
    recv, send = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=run_job, args=(src, dst, Options(quality="draft"), send))
    proc.start()
    send.close()
    msgs = []
    try:
        while True:
            msgs.append(recv.recv())
    except EOFError:
        pass
    proc.join(30)
    return msgs, proc.exitcode


def test_worker_converts_in_its_own_process(tmp_path):
    src = str(tmp_path / "s.step")
    make_sample(src)
    dst = str(tmp_path / "s.glb")
    msgs, code = _run(src, dst)
    assert code == 0
    kinds = [k for k, _ in msgs]
    assert kinds[-1] == "ok" and "log" in kinds
    assert [v[0] for k, v in msgs if k == "phase"][0] == "read"
    assert os.path.getsize(dst) > 0


def test_worker_reports_errors(tmp_path):
    bad = tmp_path / "bad.step"
    bad.write_text("nope")
    msgs, code = _run(str(bad), str(tmp_path / "bad.glb"))
    assert code == 0
    assert msgs[-1][0] == "error" and "could not read" in msgs[-1][1]
