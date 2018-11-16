# tested cpython 3.7.1 & panda3d input overhaul 2018-11-11
from . import *

# panda3d test program

import panda3d
import panda3d.core as p3d

p3d.loadPrcFileData("", "load-display pandagles2")
p3d.loadPrcFileData("", "win-origin -2 -2")
p3d.loadPrcFileData("", "win-size 848 480")
p3d.loadPrcFileData("", "support-threads #f")
p3d.loadPrcFileData("", "textures-power-2 down")
p3d.loadPrcFileData("", "textures-square down")
p3d.loadPrcFileData("", "show-frame-rate-meter #t")

import direct
import direct.task
import direct.task.TaskManagerGlobal

# from direct.task.TaskManagerGlobal import taskMgr

import direct.showbase
from direct.showbase.ShowBase import ShowBase as ShowBase


def Cube(size=1.0, geom_name="CubeMaker", gvd_name="Data", gvw_name="vertex"):
    from panda3d.core import (
        Vec3,
        GeomVertexFormat,
        GeomVertexData,
        GeomVertexWriter,
        GeomTriangles,
        Geom,
        GeomNode,
        NodePath,
        GeomPoints,
        loadPrcFileData,
    )

    format = GeomVertexFormat.getV3()
    data = GeomVertexData(gvd_name, format, Geom.UHStatic)
    vertices = GeomVertexWriter(data, gvw_name)

    size = float(size) / 2.0
    vertices.addData3f(-size, -size, -size)
    vertices.addData3f(+size, -size, -size)
    vertices.addData3f(-size, +size, -size)
    vertices.addData3f(+size, +size, -size)
    vertices.addData3f(-size, -size, +size)
    vertices.addData3f(+size, -size, +size)
    vertices.addData3f(-size, +size, +size)
    vertices.addData3f(+size, +size, +size)

    triangles = GeomTriangles(Geom.UHStatic)

    def addQuad(v0, v1, v2, v3):
        triangles.addVertices(v0, v1, v2)
        triangles.addVertices(v0, v2, v3)
        triangles.closePrimitive()

    addQuad(4, 5, 7, 6)  # Z+
    addQuad(0, 2, 3, 1)  # Z-
    addQuad(3, 7, 5, 1)  # X+
    addQuad(4, 6, 2, 0)  # X-
    addQuad(2, 6, 7, 3)  # Y+
    addQuad(0, 1, 5, 4)  # Y+

    geom = Geom(data)
    geom.addPrimitive(triangles)

    node = GeomNode(geom_name)
    node.addGeom(geom)

    return NodePath(node)


class MyApp(ShowBase):
    instance = None
    frame_time = 1.0 / 60

    async def async_loop(self):
        while not aio.is_closed():
            direct.task.TaskManagerGlobal.taskMgr.step()
            await asyncio.sleep(self.frame_time)

    def async_run(self):
        self.__class__.instance = self
        run(self.async_loop)

    # patch the sync run which would prevent to enter interactive mode
    run = async_run

    # add some colored cubes

    def build(self):
        base.cam.reparent_to(render)
        from random import random

        cube = Cube(size=1.0)

        cubes = render.attachNewNode("cubes")
        cubes.set_pos(0, 0, 0)

        for x in range(5):
            for y in range(5):
                for z in range(5):
                    instance = cube.copyTo(cubes)
                    instance.setPos(x - 2, y - 2, z - 2)
                    instance.setColor(random(), random(), random(), 1)

        base.cam.set_pos(16, 12, 30)
        base.cam.look_at(0, 0, 0)

        self.cubes = cubes

    # cube spinner

    async def update(self, dt=0):
        while not aio.is_closed():
            group = self.cubes
            h, p, r = group.get_hpr()
            group.setH(h + 1)
            group.setP(p + 1)
            group.setY(r + 1)
            await asyncio.sleep(self.frame_time)


print(
    """
- This async demo uses no threads at all -

Panda3D should have opened its default engine window by now

I have created object "MyApp" for you
You can start panda just now with :
>>> MyApp.run()

>>> MyApp.instance.build()   # to add a cube

>>> aio.create_task( MyApp.instance.update() )  # to start a spinning coroutine
or
>>> run( MyApp.instance.update ) # the same as a shortcut which can takes lists, note no ()

use pause()/resume() to hang/restart all asyncio operations
aio.close() to terminate them
meanwhile enjoy the text clock upper right on your term.
"""
)

__import__("__main__").MyApp = MyApp()
