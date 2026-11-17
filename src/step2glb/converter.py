"""Core STEP -> GLB conversion (no GUI, no argument parsing)."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Callable, Optional

from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.collections import IndexedDataMap_TCollection_AsciiString_TCollection_AsciiString as FileInfoMap
from OCP.IFSelect import IFSelect_RetDone
from OCP.Message import Message_ProgressRange
from OCP.RWGltf import RWGltf_CafWriter
from OCP.RWMesh import RWMesh_CoordinateSystem, RWMesh_CoordinateSystemConverter, RWMesh_NameFormat
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_AsciiString, TCollection_ExtendedString
from OCP.collections import Sequence_TDF_Label
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFApp import XCAFApp_Application
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool

STEP_EXTENSIONS = (".step", ".stp")

# Mesh quality presets: (relative deflection, angular deflection in radians).
# "Relative" means the allowed surface error scales with the size of each
# edge/face, so a small screw and a large housing both keep a good shape.
QUALITY_PRESETS = {
    "draft": (0.1, 0.8),
    "normal": (0.03, 0.5),
    "fine": (0.01, 0.35),
}

Logger = Callable[[str], None]
# progress(phase, fraction): phase is one of PHASES; fraction is 0..1 when the phase
# can report how far it is, None when it cannot (OpenCASCADE gives no progress to
# Python while it reads and transfers the file).
Progress = Callable[[str, Optional[float]], None]
PHASES = ("read", "transfer", "mesh", "write")


def _no_progress(phase: str, fraction: Optional[float]) -> None:
    pass


class ConversionError(Exception):
    """Raised when a file cannot be converted."""


@dataclass
class Options:
    quality: str = "normal"
    # Absolute linear deflection in model units (mm for most STEP files).
    # When set, it overrides the quality preset.
    deflection: Optional[float] = None
    # glTF is Y-up and in metres; STEP is usually Z-up and in millimetres.
    y_up: bool = True
    metres: bool = True


def is_step_file(path: str) -> bool:
    return path.lower().endswith(STEP_EXTENSIONS)


def default_output_path(src: str, out_dir: Optional[str] = None) -> str:
    base = os.path.splitext(os.path.basename(src))[0] + ".glb"
    return os.path.join(out_dir or os.path.dirname(os.path.abspath(src)), base)


def _read_step(path: str, log: Logger, progress: Progress) -> TDocStd_Document:
    app = XCAFApp_Application.GetApplication_s()
    doc = TDocStd_Document(TCollection_ExtendedString("BinXCAF"))
    app.InitDocument(doc)

    reader = STEPCAFControl_Reader()
    reader.SetColorMode(True)
    reader.SetNameMode(True)
    reader.SetLayerMode(True)
    reader.SetMatMode(True)

    progress("read", None)
    t = time.time()
    status = reader.ReadFile(path)
    if status != IFSelect_RetDone:
        raise ConversionError("OpenCASCADE could not read this file (is it a valid STEP file?)")
    log(f"Parsed the file in {time.time() - t:.1f}s")
    progress("transfer", None)
    t = time.time()
    if not reader.Transfer(doc, Message_ProgressRange()):
        raise ConversionError("The STEP file was read but its content could not be transferred")
    log(f"Built the 3D shapes in {time.time() - t:.1f}s")
    return doc


def _free_shapes(doc: TDocStd_Document):
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    labels = Sequence_TDF_Label()
    tool.GetFreeShapes(labels)
    return tool, [labels.Value(i) for i in range(1, labels.Length() + 1)]


def _parts(tool) -> list:
    """Every distinct part (non-assembly shape) of the document, each listed once
    even when it is used many times."""
    labels = Sequence_TDF_Label()
    tool.GetShapes(labels)
    return [tool.GetShape_s(labels.Value(i)) for i in range(1, labels.Length() + 1)
            if not XCAFDoc_ShapeTool.IsAssembly_s(labels.Value(i))]


def _mesh(doc: TDocStd_Document, opts: Options, log: Logger, progress: Progress) -> None:
    tool, roots = _free_shapes(doc)
    if not roots:
        raise ConversionError("The file contains no 3D shapes")

    if opts.deflection is not None:
        defl, ang, relative = opts.deflection, QUALITY_PRESETS["normal"][1], False
        desc = f"absolute deflection {defl:g}"
    else:
        defl, ang = QUALITY_PRESETS[opts.quality]
        relative = True
        desc = f"quality '{opts.quality}'"
    parts = _parts(tool)
    log(f"Meshing {len(parts)} parts ({desc}, using all CPU cores)...")
    # One part at a time, so the progress is real; each call still meshes the
    # faces of the part in parallel, and it is as fast as meshing everything at once.
    progress("mesh", 0.0)
    shown = 0
    for i, shape in enumerate(parts, 1):
        BRepMesh_IncrementalMesh(shape, defl, relative, ang, True)  # last arg: parallel
        pct = i * 100 // len(parts)
        if pct != shown:
            shown = pct
            progress("mesh", i / len(parts))
    # Safety net for shapes that are not stored as parts: faces meshed above are skipped.
    for label in roots:
        BRepMesh_IncrementalMesh(tool.GetShape_s(label), defl, relative, ang, True)
    progress("mesh", 1.0)


def convert(src: str, dst: str, opts: Optional[Options] = None, log: Logger = print,
            progress: Optional[Progress] = None) -> dict:
    """Convert one STEP file to a binary glTF (.glb). Returns basic stats."""
    opts = opts or Options()
    progress = progress or _no_progress
    if opts.quality not in QUALITY_PRESETS:
        raise ConversionError(f"Unknown quality '{opts.quality}'")
    if not os.path.isfile(src):
        raise ConversionError(f"File not found: {src}")

    t0 = time.time()
    size_mb = os.path.getsize(src) / 1e6
    log(f"Reading {os.path.basename(src)} ({size_mb:.1f} MB)...")
    doc = _read_step(src, log, progress)
    t_read = time.time()
    log(f"Read in {t_read - t0:.1f}s")

    _mesh(doc, opts, log, progress)
    t_mesh = time.time()
    log(f"Meshed in {t_mesh - t_read:.1f}s")

    log("Writing GLB...")
    progress("write", None)
    converter = RWMesh_CoordinateSystemConverter()
    # STEP documents read by OpenCASCADE are in millimetres.
    converter.SetInputLengthUnit(0.001)
    converter.SetOutputLengthUnit(1.0 if opts.metres else 0.001)
    converter.SetInputCoordinateSystem(RWMesh_CoordinateSystem.RWMesh_CoordinateSystem_Zup)
    if opts.y_up:
        converter.SetOutputCoordinateSystem(RWMesh_CoordinateSystem.RWMesh_CoordinateSystem_Yup)
    else:
        converter.SetOutputCoordinateSystem(RWMesh_CoordinateSystem.RWMesh_CoordinateSystem_Zup)

    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    tmp = dst + ".part"
    writer = RWGltf_CafWriter(TCollection_AsciiString(tmp), True)
    writer.SetCoordinateSystemConverter(converter)
    writer.SetParallel(True)
    # One glTF primitive per part (per colour) instead of one per B-Rep face: otherwise
    # viewers get one object per face, which breaks exploded views and is very slow.
    writer.SetMergeFaces(True)
    # Prefer the part (product) name; fall back to the instance name.
    writer.SetNodeNameFormat(RWMesh_NameFormat.RWMesh_NameFormat_ProductOrInstance)
    writer.SetMeshNameFormat(RWMesh_NameFormat.RWMesh_NameFormat_ProductOrInstance)
    ok = writer.Perform(doc, FileInfoMap(), Message_ProgressRange())
    if not ok or not os.path.isfile(tmp):
        if os.path.isfile(tmp):
            os.remove(tmp)
        raise ConversionError("Writing the GLB failed")
    os.replace(tmp, dst)
    progress("write", 1.0)

    out_mb = os.path.getsize(dst) / 1e6
    total = time.time() - t0
    log(f"Done: {os.path.basename(dst)} ({out_mb:.1f} MB) in {total:.1f}s")
    return {"seconds": total, "input_mb": size_mb, "output_mb": out_mb}


def collect_inputs(paths, recursive: bool = False):
    """Expand files and folders into a sorted list of STEP files."""
    found = []
    for p in paths:
        if os.path.isdir(p):
            if recursive:
                for root, _dirs, files in os.walk(p):
                    found += [os.path.join(root, f) for f in files if is_step_file(f)]
            else:
                found += [os.path.join(p, f) for f in os.listdir(p) if is_step_file(f)]
        elif is_step_file(p):
            found.append(p)
    return sorted(dict.fromkeys(found))
