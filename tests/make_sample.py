"""Generate a small coloured, named STEP assembly for tests and CI smoke checks."""

import sys

from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.gp import gp_Trsf, gp_Vec
from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDocStd import TDocStd_Document
from OCP.TopLoc import TopLoc_Location
from OCP.XCAFApp import XCAFApp_Application
from OCP.XCAFDoc import XCAFDoc_ColorType, XCAFDoc_DocumentTool


def make_sample(path: str, extra_instances: int = 0) -> None:
    app = XCAFApp_Application.GetApplication_s()
    doc = TDocStd_Document(TCollection_ExtendedString("BinXCAF"))
    app.InitDocument(doc)
    shapes = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    colors = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())

    box = shapes.AddShape(BRepPrimAPI_MakeBox(40, 30, 20).Shape(), False)
    cyl = shapes.AddShape(BRepPrimAPI_MakeCylinder(8, 50).Shape(), False)
    TDataStd_Name.Set_s(box, TCollection_ExtendedString("Box"))
    TDataStd_Name.Set_s(cyl, TCollection_ExtendedString("Cylinder"))
    colors.SetColor(box, Quantity_Color(0.9, 0.1, 0.1, Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)
    colors.SetColor(cyl, Quantity_Color(0.1, 0.2, 0.9, Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)

    asm = shapes.NewShape()
    TDataStd_Name.Set_s(asm, TCollection_ExtendedString("Assembly"))
    shapes.AddComponent(asm, box, TopLoc_Location())
    move = gp_Trsf()
    move.SetTranslation(gp_Vec(60, 0, 0))
    shapes.AddComponent(asm, cyl, TopLoc_Location(move))
    # Optional stress test: many instances of curved parts.
    if extra_instances:
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeSphere, BRepPrimAPI_MakeTorus

        protos = [
            shapes.AddShape(BRepPrimAPI_MakeSphere(10 + i).Shape(), False) for i in range(3)
        ] + [shapes.AddShape(BRepPrimAPI_MakeTorus(20, 4).Shape(), False)]
        for i in range(extra_instances):
            t = gp_Trsf()
            t.SetTranslation(gp_Vec((i % 50) * 50, (i // 50 % 50) * 50, (i // 2500) * 50))
            shapes.AddComponent(asm, protos[i % len(protos)], TopLoc_Location(t))
    shapes.UpdateAssemblies()

    writer = STEPCAFControl_Writer()
    writer.SetColorMode(True)
    writer.SetNameMode(True)
    writer.Transfer(doc)
    if writer.Write(path) != IFSelect_RetDone:
        raise RuntimeError("could not write sample STEP")


if __name__ == "__main__":
    make_sample(
        sys.argv[1] if len(sys.argv) > 1 else "sample.step",
        int(sys.argv[2]) if len(sys.argv) > 2 else 0,
    )
