import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))

import pytest
from make_sample import make_sample

from step2glb.cli import run
from step2glb.converter import ConversionError, Options, collect_inputs, convert, default_output_path


def read_gltf_json(path):
    data = open(path, "rb").read()
    magic, version, length = struct.unpack("<4sII", data[:12])
    assert magic == b"glTF" and version == 2 and length == len(data)
    chunk_len, chunk_type = struct.unpack("<I4s", data[12:20])
    assert chunk_type == b"JSON"
    return json.loads(data[20:20 + chunk_len])


@pytest.fixture(scope="module")
def sample(tmp_path_factory):
    path = tmp_path_factory.mktemp("data") / "sample.step"
    make_sample(str(path))
    return str(path)


def test_convert_keeps_names_colours_hierarchy_and_units(sample, tmp_path):
    out = str(tmp_path / "out.glb")
    convert(sample, out, log=lambda m: None)
    g = read_gltf_json(out)
    names = [n.get("name") for n in g["nodes"]]
    assert names == ["Assembly", "Box", "Cylinder"]
    assert len(g["materials"]) == 2
    root = g["nodes"][0]
    assert root["children"] == [1, 2]
    # Cylinder was moved 60 mm along X -> 0.06 m (metres, glTF)
    assert g["nodes"][2]["translation"][0] == pytest.approx(0.06)
    # Cylinder is 50 mm tall along STEP Z -> glTF Y (Y-up)
    ys = [a["max"][1] for a in g["accessors"] if a["type"] == "VEC3" and "max" in a]
    assert max(ys) == pytest.approx(0.05)


def test_one_primitive_per_part_not_per_face(sample, tmp_path):
    # The box has 6 faces and the cylinder 3: viewers must get one object per part,
    # otherwise exploded views pull the faces apart.
    out = str(tmp_path / "merged.glb")
    convert(sample, out, log=lambda m: None)
    g = read_gltf_json(out)
    assert [len(m["primitives"]) for m in g["meshes"]] == [1, 1]


def test_progress_reports_phases_in_order(sample, tmp_path):
    seen = []
    convert(sample, str(tmp_path / "p.glb"), log=lambda m: None,
            progress=lambda phase, frac: seen.append((phase, frac)))
    phases = [p for p, _ in seen]
    assert [p for i, p in enumerate(phases) if i == 0 or phases[i - 1] != p] == ["read", "transfer", "mesh", "write"]
    mesh = [f for p, f in seen if p == "mesh"]
    assert mesh[0] == 0.0 and mesh[-1] == 1.0 and mesh == sorted(mesh)
    assert seen[-1] == ("write", 1.0)


def test_millimetres_and_z_up(sample, tmp_path):
    out = str(tmp_path / "mm.glb")
    convert(sample, out, Options(y_up=False, metres=False), log=lambda m: None)
    g = read_gltf_json(out)
    assert g["nodes"][2]["translation"][0] == pytest.approx(60.0)
    zs = [a["max"][2] for a in g["accessors"] if a["type"] == "VEC3" and "max" in a]
    assert max(zs) == pytest.approx(50.0)


def test_invalid_file_raises_and_leaves_no_output(tmp_path):
    bad = tmp_path / "bad.step"
    bad.write_text("this is not a STEP file")
    out = tmp_path / "bad.glb"
    with pytest.raises(ConversionError):
        convert(str(bad), str(out), log=lambda m: None)
    assert not out.exists()
    assert not (tmp_path / "bad.glb.part").exists()


def test_collect_inputs_and_output_path(sample, tmp_path):
    folder = os.path.dirname(sample)
    assert collect_inputs([folder]) == [sample]
    assert collect_inputs([sample, sample]) == [sample]
    assert default_output_path(sample).endswith("sample.glb")
    assert default_output_path(sample, str(tmp_path)) == str(tmp_path / "sample.glb")


def test_cli_batch_with_out_dir_and_skip(sample, tmp_path, capsys):
    out_dir = tmp_path / "glb"
    assert run([sample, "-o", str(out_dir), "-q", "draft"]) == 0
    assert (out_dir / "sample.glb").is_file()
    assert run([sample, "-o", str(out_dir), "--skip-existing"]) == 0
    assert "skipped" in capsys.readouterr().out


def test_cli_reports_failure_exit_code(tmp_path):
    bad = tmp_path / "bad.stp"
    bad.write_text("nope")
    assert run([str(bad)]) == 1
