#   (c) Juergen Riegel (FreeCAD@juergen-riegel.net) 2011      LGPL        *
#                                                                         *
#   This file is part of the FreeCAD CAx development system.              *
#                                                                         *
#   This program is free software; you can redistribute it and/or modify  *
#   it under the terms of the GNU Lesser General Public License (LGPL)    *
#   as published by the Free Software Foundation; either version 2 of     *
#   the License, or (at your option) any later version.                   *
#   for detail see the LICENCE text file.                                 *
#                                                                         *
#   FreeCAD is distributed in the hope that it will be useful,            *
#   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#   GNU Library General Public License for more details.                  *
#                                                                         *
#   You should have received a copy of the GNU Library General Public     *
#   License along with FreeCAD; if not, write to the Free Software        *
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#   USA                                                                   *
#**************************************************************************

import FreeCAD, unittest, Part
import copy
import math
from FreeCAD import Units
from FreeCAD import Base
App = FreeCAD

from parttests.regression_tests import RegressionTests

#---------------------------------------------------------------------------
# define the test cases to test the FreeCAD Part module
#---------------------------------------------------------------------------
def getCoincidentVertexes(vtx1, vtx2):
    pairs = []
    tol = Part.Precision.confusion()
    for i in vtx1:
        for j in vtx2:
            if i.Point.distanceToPoint(j.Point) < tol:
                pairs.append((i, j))

    return pairs


class PartTestCases(unittest.TestCase):
    def setUp(self):
        self.Doc = FreeCAD.newDocument("PartTest")

    def testBoxCase(self):
        self.Box = self.Doc.addObject("Part::Box","Box")
        self.Doc.recompute()
        self.failUnless(len(self.Box.Shape.Faces)==6)

    def testIssue2985(self):
        v1 = App.Vector(0.0,0.0,0.0)
        v2 = App.Vector(10.0,0.0,0.0)
        v3 = App.Vector(10.0,0.0,10.0)
        v4 = App.Vector(0.0,0.0,10.0)
        edge1 = Part.makeLine(v1, v2)
        edge2 = Part.makeLine(v2, v3)
        edge3 = Part.makeLine(v3, v4)
        edge4 = Part.makeLine(v4, v1)
        # Travis build confirms the crash under macOS
        #result = Part.makeFilledFace([edge1,edge2,edge3,edge4])
        #self.Doc.addObject("Part::Feature","Face").Shape = result
        #self.assertTrue(isinstance(result.Surface, Part.BSplineSurface))

    def tearDown(self):
        #closing doc
        FreeCAD.closeDocument("PartTest")
        #print ("omit closing document for debugging")

class PartTestBSplineCurve(unittest.TestCase):
    def setUp(self):
        self.Doc = FreeCAD.newDocument("PartTest")

        poles = [[0, 0, 0], [1, 1, 0], [2, 0, 0]]
        self.spline = Part.BSplineCurve()
        self.spline.buildFromPoles(poles)

        poles = [[0, 0, 0], [1, 1, 0], [2, 0, 0], [1, -1, 0]]
        self.nurbs = Part.BSplineCurve()
        self.nurbs.buildFromPolesMultsKnots(poles, (3, 1, 3),(0, 0.5, 1), False, 2)

    def testProperties(self):
        self.assertEqual(self.spline.Continuity, 'CN')
        self.assertEqual(self.spline.Degree, 2)
        self.assertEqual(self.spline.EndPoint, App.Vector(2, 0, 0))
        self.assertEqual(self.spline.FirstParameter, 0.0)
        self.assertEqual(self.spline.FirstUKnotIndex, 1)
        self.assertEqual(self.spline.KnotSequence, [0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
        self.assertEqual(self.spline.LastParameter, 1.0)
        self.assertEqual(self.spline.LastUKnotIndex, 2)
        max_degree = self.spline.MaxDegree
        self.assertEqual(self.spline.NbKnots, 2)
        self.assertEqual(self.spline.NbPoles, 3)
        self.assertEqual(self.spline.StartPoint, App.Vector(0.0, 0.0, 0.0))

    def testGetters(self):
        '''only check if the function doesn't crash'''
        self.spline.getKnot(1)
        self.spline.getKnots()
        self.spline.getMultiplicities()
        self.spline.getMultiplicity(1)
        self.spline.getPole(1)
        self.spline.getPoles()
        self.spline.getPolesAndWeights()
        self.spline.getResolution(0.5)
        self.spline.getWeight(1)
        self.spline.getWeights()

    def testSetters(self):
        spline = copy.copy(self.spline)
        spline.setKnot(1, 0.1)
        spline.setPeriodic()
        spline.setNotPeriodic()
        # spline.setKnots()
        # spline.setOrigin(2)   # not working?
        self.spline.setPole(1, App.Vector([1, 0, 0])) # first parameter 0 gives occ error

    def testIssue2671(self):
        self.Doc = App.newDocument("Issue2671")
        Box = self.Doc.addObject("Part::Box","Box")
        Mirroring = self.Doc.addObject("Part::Mirroring", 'Mirroring')
        Spreadsheet = self.Doc.addObject('Spreadsheet::Sheet', 'Spreadsheet')
        Mirroring.Source = Box
        Mirroring.Base = (8, 5, 25)
        Mirroring.Normal = (0.5, 0.2, 0.9)
        Spreadsheet.set('A1', '=Mirroring.Base.x')
        Spreadsheet.set('B1', '=Mirroring.Base.y')
        Spreadsheet.set('C1', '=Mirroring.Base.z')
        Spreadsheet.set('A2', '=Mirroring.Normal.x')
        Spreadsheet.set('B2', '=Mirroring.Normal.y')
        Spreadsheet.set('C2', '=Mirroring.Normal.z')
        self.Doc.recompute()
        self.assertEqual(Spreadsheet.A1, Units.Quantity('8 mm'))
        self.assertEqual(Spreadsheet.B1, Units.Quantity('5 mm'))
        self.assertEqual(Spreadsheet.C1, Units.Quantity('25 mm'))
        self.assertEqual(Spreadsheet.A2, Units.Quantity('0.5 mm'))
        self.assertEqual(Spreadsheet.B2, Units.Quantity('0.2 mm'))
        self.assertEqual(Spreadsheet.C2, Units.Quantity('0.9 mm'))
        App.closeDocument("Issue2671")

    def testIssue2876(self):
        self.Doc = App.newDocument("Issue2876")
        Cylinder = self.Doc.addObject("Part::Cylinder", "Cylinder")
        Cylinder.Radius = 5
        Pipe = self.Doc.addObject("Part::Thickness", "Pipe")
        Pipe.Faces = (Cylinder, ["Face2", "Face3"])
        Pipe.Mode = 1
        Pipe.Value = -1 # negative wall thickness
        Spreadsheet = self.Doc.addObject('Spreadsheet::Sheet', 'Spreadsheet')
        Spreadsheet.set('A1', 'Pipe OD')
        Spreadsheet.set('B1', 'Pipe WT')
        Spreadsheet.set('C1', 'Pipe ID')
        Spreadsheet.set('A2', '=2*Cylinder.Radius')
        Spreadsheet.set('B2', '=-Pipe.Value')
        Spreadsheet.set('C2', '=2*(Cylinder.Radius + Pipe.Value)')
        self.Doc.recompute()
        self.assertEqual(Spreadsheet.B2, Units.Quantity('1 mm'))
        self.assertEqual(Spreadsheet.C2, Units.Quantity('8 mm'))
        App.closeDocument("Issue2876")

    def testSubElements(self):
        box = Part.makeBox(1, 1, 1)
        with self.assertRaises(ValueError):
            box.getElement("InvalidName")
        with self.assertRaises(ValueError):
            box.getElement("Face6_abc")
        with self.assertRaises(Part.OCCError):
            box.getElement("Face7")

    def tearDown(self):
        #closing doc
        FreeCAD.closeDocument("PartTest")

class PartTestNormals(unittest.TestCase):
    def setUp(self):
        self.face = Part.makePlane(1, 1)

    def testFaceNormal(self):
        self.assertEqual(self.face.normalAt(0, 0), Base.Vector(0, 0, 1))
        self.assertEqual(self.face.Surface.normal(0, 0), Base.Vector(0, 0, 1))

    def testReverseOrientation(self):
        self.face.reverse()
        self.assertEqual(self.face.normalAt(0, 0), Base.Vector(0, 0, -1))
        self.assertEqual(self.face.Surface.normal(0, 0), Base.Vector(0, 0, 1))

    def testPlacement(self):
        self.face.reverse()
        self.face.Placement.Rotation.Angle = 1
        self.face.Placement.Rotation.Axis = (1,1,1)
        vec = Base.Vector(-0.63905, 0.33259, -0.69353)
        self.assertGreater(self.face.normalAt(0, 0).dot(vec), 0.9999)
        self.assertLess(self.face.Surface.normal(0, 0).dot(vec), -0.9999)

    def tearDown(self):
        pass

class PartTestCircle2D(unittest.TestCase):
    def testValidCircle(self):
        p1 = App.Base.Vector2d(0.01, 0.01)
        p2 = App.Base.Vector2d(0.02, 0.02)
        p3 = App.Base.Vector2d(0.01, -0.01)
        Part.Geom2d.Circle2d.getCircleCenter(p1, p2, p3)

    def testCollinearPoints(self):
        p1 = App.Base.Vector2d(0.01, 0.01)
        p2 = App.Base.Vector2d(0.02, 0.02)
        p3 = App.Base.Vector2d(0.04, 0.0399)
        with self.assertRaises(ValueError):
            Part.Geom2d.Circle2d.getCircleCenter(p1, p2, p3)

class PartTestCone(unittest.TestCase):
    def testderivatives(self):
        def get_dn(surface, u, v):
            pos = surface.value(u, v)
            v10 = surface.getDN(u, v, 1, 0)
            v01 = surface.getDN(u, v, 0, 1)
            v11 = surface.getDN(u, v, 1, 1)
            return (pos, v10, v01, v11)

        cone = Part.Cone()
        cone.SemiAngle = 0.2
        cone.Radius = 2.0

        u, v = (5.0, 5.0)
        vp, v1, v2, v3 = get_dn(cone, u, v)

        shape = cone.toShape(0, 2*math.pi, 0, 10)
        shape = shape.toNurbs()
        spline = shape.Face1.Surface

        u, v = spline.parameter(vp)
        wp, w1, w2, w3 = get_dn(spline, u, v)

        self.assertAlmostEqual(vp.distanceToPoint(wp), 0)
        self.assertAlmostEqual(v1.getAngle(w1), 0)
        self.assertAlmostEqual(v2.getAngle(w2), 0)
        self.assertAlmostEqual(v3.getAngle(w3), 0)

class PartTestChFi2dAlgos(unittest.TestCase):
    def testChFi2d_FilletAlgo(self):
        v = FreeCAD.Vector
        edge1 = Part.makeLine(v(0,0,0), v(0,10,0))
        edge2 = Part.makeLine(v(0,10,0), v(10,10,0))
        wire = Part.Wire([edge1, edge2])
        pln = Part.Plane()

        with self.assertRaises(TypeError):
            alg = Part.ChFi2d.FilletAlgo(pln)

        alg = Part.ChFi2d.FilletAlgo()
        with self.assertRaises(TypeError):
            alg.init()

        print (alg)
        # Test without shape
        with self.assertRaises(Base.CADKernelError):
            alg.perform(1)

        with self.assertRaises(TypeError):
            alg.perform()

        alg = Part.ChFi2d.FilletAlgo(wire, pln)
        alg.init(edge1, edge2, pln)
        alg.init(wire, pln)

        alg = Part.ChFi2d.FilletAlgo(edge1, edge2, pln)
        alg.perform(1.0)

        with self.assertRaises(TypeError):
            alg.numberOfResults()

        with self.assertRaises(TypeError):
            alg.result(1)

        self.assertEqual(alg.numberOfResults(Base.Vector(0,10,0)), 1)
        result = alg.result(Base.Vector(0,10,0))
        curve = result[0].Curve
        self.assertEqual(type(curve), Part.Circle)
        self.assertEqual(curve.Axis, pln.Axis)
        self.assertEqual(curve.Radius, 1.0)

    def testChFi2d_AnaFilletAlgo(self):
        v = FreeCAD.Vector
        edge1 = Part.makeLine(v(0,0,0), v(0,10,0))
        edge2 = Part.makeLine(v(0,10,0), v(10,10,0))
        wire = Part.Wire([edge1, edge2])
        pln = Part.Plane()

        with self.assertRaises(TypeError):
            alg = Part.ChFi2d.AnaFilletAlgo(pln)

        alg = Part.ChFi2d.AnaFilletAlgo()
        with self.assertRaises(TypeError):
            alg.init()

        print (alg)
        # Test without shape
        self.assertFalse(alg.perform(1))

        with self.assertRaises(TypeError):
            alg.perform()

        alg = Part.ChFi2d.AnaFilletAlgo(wire, pln)
        alg.init(edge1, edge2, pln)
        alg.init(wire, pln)

        alg = Part.ChFi2d.AnaFilletAlgo(edge1, edge2, pln)
        alg.perform(1.0)

        with self.assertRaises(TypeError):
            alg.result(1)

        result = alg.result()
        curve = result[0].Curve
        self.assertEqual(type(curve), Part.Circle)
        self.assertEqual(curve.Radius, 1.0)

    def testChFi2d_ChamferAPI(self):
        v = FreeCAD.Vector
        edge1 = Part.makeLine(v(0,0,0), v(0,10,0))
        edge2 = Part.makeLine(v(0,10,0), v(10,10,0))
        wire = Part.Wire([edge1, edge2])

        with self.assertRaises(TypeError):
            alg = Part.ChFi2d.ChamferAPI(edge1)

        alg = Part.ChFi2d.ChamferAPI(wire)
        with self.assertRaises(TypeError):
            alg.init()

        print (alg)

        with self.assertRaises(TypeError):
            alg.perform(1)

        alg = Part.ChFi2d.ChamferAPI(wire)
        alg.init(edge1, edge2)
        alg.init(wire)

        alg = Part.ChFi2d.ChamferAPI(edge1, edge2)
        alg.perform()

        with self.assertRaises(TypeError):
            alg.result(1)

        result = alg.result(1.0, 1.0)
        curve = result[0].Curve
        self.assertEqual(type(curve), Part.Line)

class PartTestRuledSurface(unittest.TestCase):
    def setUp(self):
        self.Doc = FreeCAD.newDocument()

    def testRuledSurfaceFromTwoObjects(self):
        line1 = Part.makeLine(FreeCAD.Vector(-70,-30,0), FreeCAD.Vector(-50,40,0))
        line2 = Part.makeLine(FreeCAD.Vector(-40,-30,0), FreeCAD.Vector(-40,10,0))
        plm1 = FreeCAD.Placement()
        plm1.Rotation = FreeCAD.Rotation(0.7071067811865476, 0.0, 0.0, 0.7071067811865475)
        line1.Placement = plm1
        fea1 = self.Doc.addObject("Part::Feature")
        fea2 = self.Doc.addObject("Part::Feature")
        fea1.Shape = line1
        fea2.Shape = line2
        ruled = self.Doc.addObject("Part::RuledSurface")
        ruled.Curve1 = fea1
        ruled.Curve2 = fea2

        self.Doc.recompute()

        same1 = getCoincidentVertexes(fea1.Shape.Vertexes, ruled.Shape.Vertexes)
        same2 = getCoincidentVertexes(fea2.Shape.Vertexes, ruled.Shape.Vertexes)
        self.assertEqual(len(same1), 2)
        self.assertEqual(len(same2), 2)

    def testRuledSurfaceFromOneObjects(self):
        sketch = self.Doc.addObject('Sketcher::SketchObject', 'Sketch')
        sketch.Placement = FreeCAD.Placement(FreeCAD.Vector(0.000000, 0.000000, 0.000000), App.Rotation(0.707107, 0.000000, 0.000000, 0.707107))
        sketch.MapMode = "Deactivated"

        sketch.addGeometry(Part.LineSegment(App.Vector(-43.475811,34.364464,0),App.Vector(-65.860519,-20.078733,0)),False)
        sketch.addGeometry(Part.LineSegment(App.Vector(14.004498,27.390331,0),App.Vector(33.577049,-27.952749,0)),False)

        ruled = self.Doc.addObject('Part::RuledSurface', 'Ruled Surface')
        ruled.Curve1 = (sketch,['Edge1'])
        ruled.Curve2 = (sketch,['Edge2'])
        self.Doc.recompute()

        same = getCoincidentVertexes(sketch.Shape.Vertexes, ruled.Shape.Vertexes)
        self.assertEqual(len(same), 4)

    def tearDown(self):
        FreeCAD.closeDocument(self.Doc.Name)
