import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))

import make_multibody
from make_sample import make_sample

from step2glb.cli import run
from step2glb.converter import Options, convert


def _parts(glb):
    d = open(glb, "rb").read()
    n = struct.unpack("<I", d[12:16])[0]
    g = json.loads(d[20:20 + n])
    nodes = [nd for nd in g["nodes"] if "mesh" in nd]
    colours = {tuple(round(c, 2) for c in m["pbrMetallicRoughness"]["baseColorFactor"][:3])
               for m in g.get("materials", [])}
    prims = [len(g["meshes"][nd["mesh"]]["primitives"]) for nd in nodes]
    return [nd.get("name") for nd in nodes], colours, prims


def _convert(tmp_path, make, opts=None):
    src = str(tmp_path / "in.step")
    make(src)
    out = str(tmp_path / "out.glb")
    logs = []
    convert(src, out, opts or Options(), log=logs.append)
    return _parts(out), logs


def test_multi_body_part_becomes_one_part_per_solid(tmp_path):
    (names, colours, prims), logs = _convert(tmp_path, make_multibody.multi_body)
    # 4 solids -> 4 parts, each one piece with its own colour; the construction line is no part
    assert names == ["Part 001", "Part 002", "Part 003", "Part 004"]
    assert prims == [1, 1, 1, 1]
    assert colours == {(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0)}
    assert any("into 4 parts" in m for m in logs)


def test_multi_body_kept_together_on_request(tmp_path):
    (names, colours, _), _ = _convert(tmp_path, make_multibody.multi_body, Options(split_bodies=False))
    assert names == ["jbgi-None"]
    assert len(colours) == 4


def test_cli_keep_bodies(tmp_path):
    src = str(tmp_path / "m.step")
    make_multibody.multi_body(src)
    assert run([src, "--keep-bodies", "-q", "draft"]) == 0
    assert _parts(str(tmp_path / "m.glb"))[0] == ["jbgi-None"]


def test_surfaces_are_never_split_into_faces(tmp_path):
    for make in (make_multibody.loose_faces, make_multibody.one_shell):
        (names, _, prims), logs = _convert(tmp_path, make)
        assert len(names) == 1 and prims == [1], make.__name__
        assert not any("Separated" in m for m in logs)


def test_real_assemblies_are_unchanged(tmp_path):
    (names, _, _), logs = _convert(tmp_path, make_sample)
    assert len(names) == 2 and "Part 001" not in names
    assert not any("Separated" in m for m in logs)
