"""STEP files for the multi-body tests (generated, so the repo stays small)."""
from OCP.BRep import BRep_Builder
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeSphere
from OCP.gp import gp_Pnt
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDocStd import TDocStd_Document
from OCP.TopAbs import TopAbs_FACE, TopAbs_SHELL
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS_Compound
from OCP.XCAFApp import XCAFApp_Application
from OCP.XCAFDoc import XCAFDoc_ColorType, XCAFDoc_DocumentTool


def _compound(*shapes):
    b = BRep_Builder()
    c = TopoDS_Compound()
    b.MakeCompound(c)
    for s in shapes:
        b.Add(c, s)
    return c


def _doc():
    doc = TDocStd_Document(TCollection_ExtendedString("BinXCAF"))
    XCAFApp_Application.GetApplication_s().InitDocument(doc)
    return doc, XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()), XCAFDoc_DocumentTool.ColorTool_s(doc.Main())


def _write(doc, path):
    w = STEPCAFControl_Writer()
    w.SetColorMode(True)
    w.SetNameMode(True)
    w.Transfer(doc)
    w.Write(path)


def multi_body(path):
    """One unnamed-solid part ("jbgi-None") holding 4 coloured solids and a construction line."""
    box = BRepPrimAPI_MakeBox(10, 10, 10).Shape()
    box2 = BRepPrimAPI_MakeBox(gp_Pnt(20, 0, 0), 5, 5, 5).Shape()
    cyl = BRepPrimAPI_MakeCylinder(3, 20).Shape()
    sph = BRepPrimAPI_MakeSphere(gp_Pnt(40, 0, 0), 4).Shape()
    line = BRepBuilderAPI_MakeEdge(gp_Pnt(0, 0, 30), gp_Pnt(10, 0, 30)).Edge()
    doc, st, ct = _doc()
    label = st.AddShape(_compound(box, box2, _compound(cyl, sph), line), False)
    TDataStd_Name.Set_s(label, TCollection_ExtendedString("jbgi-None"))
    for s, rgb in ((box, (1, 0, 0)), (box2, (0, 1, 0)), (cyl, (0, 0, 1)), (sph, (1, 1, 0))):
        ct.SetColor(st.AddSubShape(label, s), Quantity_Color(*rgb, Quantity_TOC_RGB),
                    XCAFDoc_ColorType.XCAFDoc_ColorSurf)
    _write(doc, path)


def loose_faces(path):
    """The 6 faces of a box as a compound, no solid: must stay one part."""
    faces = []
    e = TopExp_Explorer(BRepPrimAPI_MakeBox(10, 10, 10).Shape(), TopAbs_FACE)
    while e.More():
        faces.append(e.Current())
        e.Next()
    doc, st, _ = _doc()
    st.AddShape(_compound(*faces), False)
    _write(doc, path)


def one_shell(path):
    doc, st, _ = _doc()
    st.AddShape(TopExp_Explorer(BRepPrimAPI_MakeBox(10, 10, 10).Shape(), TopAbs_SHELL).Current(), False)
    _write(doc, path)
