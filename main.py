import os.path
import tkinter.filedialog
import tkinter.simpledialog
from direct.gui.DirectButton import DirectButton
from panda3d.core import *

from direct.showbase.ShowBase import ShowBase

import util

default_target_path = "data/skin.obj"
sphere_path = "data/sphere.obj"


class App(ShowBase):
    def __init__(self):
        ShowBase.__init__(self, windowType='none')

        self.source_parent_node = NodePath("source_parent")
        self.source_parent_node.reparentTo(self.render)
        self.feature_point_parent_node = NodePath("feature_parent")
        self.feature_point_parent_node.reparentTo(self.source_parent_node)

        self.source_mesh_node = None
        self.source_pc_node = None

        self.start_tk()

        frame = self.tkRoot
        frame.geometry('1280x960')
        frame.title('PointCLoudColoring')

        frame.update()

        frame_id = frame.winfo_id()
        width = frame.winfo_width()
        height = frame.winfo_height()

        props = WindowProperties()
        props.setForeground(True)
        props.setParentWindow(frame_id)
        props.setOrigin(0, 0)
        props.setSize(width, height)

        self.makeDefaultPipe()
        self.openDefaultWindow(props=props)
        self.setFrameRateMeter(True)

        '''set panda3d scene'''
        # Disable the default DisplayRegion, which covers the whole screen.
        dr = self.camNode.getDisplayRegion(0)
        dr.setActive(0)

        # Now, make a new pair of side-by-side DisplayRegions.
        window = dr.getWindow()

        self.view = window.makeDisplayRegion(0, 3 / 4, 0, 1)
        self.view.setSort(dr.getSort())
        self.view.setClearColorActive(True)
        self.view.setClearColor((0.4, 0.4, 0.4, 0.4))

        self.ui_view = window.makeDisplayRegion(3 / 4, 1, 0, 1)
        self.ui_view.setSort(dr.getSort())
        self.ui_view.setClearColorActive(True)
        self.ui_view.setClearColor((0.5, 0.5, 0, 1))

        camera2d = NodePath(Camera('cam2d'))
        lens = OrthographicLens()
        lens.setFilmSize(2, 2)
        lens.setNearFar(-1000, 1000)
        camera2d.node().setLens(lens)

        render2d = NodePath('render2d')
        render2d.setDepthTest(False)
        render2d.setDepthWrite(False)
        camera2d.reparentTo(render2d)
        self.ui_view.setCamera(camera2d)

        aspect2d = render2d.attachNewNode(PGTop('aspect2d'))
        mw_node = MouseWatcher("mouse_watcher")
        mw_node.set_display_region(self.ui_view)
        input_ctrl = self.mouseWatcher.parent
        mw = input_ctrl.attach_new_node(mw_node)
        bt_node = ButtonThrower("btn_thrower")
        mw.attach_new_node(bt_node)
        aspect2d.node().setMouseWatcher(mw_node)

        DirectButton(text=["change source pc"], parent=aspect2d, frameSize=(-.5, .5, -.05, .1), text_scale=0.1,
                     pos=(0, 0, 0.2), command=self.change_source_pc)
        DirectButton(text=["color point cloud"], parent=aspect2d, frameSize=(-.5, .5, -.05, .1), text_scale=0.1,
                     pos=(0, 0, 0), command=self.color_pointcloud)
        DirectButton(text=["save colored pc"], parent=aspect2d, frameSize=(-.5, .5, -.05, .1), text_scale=0.1,
                     pos=(0, 0, -0.2), command=self.save_colored_pc)

        self.setLight()
        self.setCamera()

        self.load(default_target_path)


    def change_source_pc(self):
        file = tkinter.filedialog.askopenfilename(initialdir="/", title="Select file")
        if file != '':
            self.load(file)


    def color_pointcloud(self):
        # TODO: make simple dialog support multiple inputs
        # input_param = tkinter.simpledialog.askstring("Input Dialog", "Feature Point + Radius (split by space)",
        #                                              parent=self.tkRoot)
        #
        # if input_param is None:
        #     return
        #
        # flist = str(input_param).split(' ')
        # flist = list(map(float, flist))
        #
        # if len(flist) != 4:
        #     print("input should have 4 elements (feature x, y, z radius)")
        #     return
        #
        # pos = [flist[0], flist[1], flist[2]]
        # radius = flist[3]
        #
        # new_node = util.color_point_cloud(self.source_pc_node, [[pos, radius]])

        feature_points = [
            [[0.05720277, 0.2442303, 0.1989999], 0.08],
            [[0.322737, 0.2498799, 0.1969999], 0.08]
        ]

        new_node = util.color_point_cloud(self.source_pc_node, feature_points)
        self.source_pc_node.removeNode()
        self.source_pc_node = new_node
        self.source_pc_node.reparentTo(self.source_parent_node)

        for child in self.feature_point_parent_node.children:
            child.removeNode()

        for feature_point in feature_points:
            pos = feature_point[0]
            sphere = self.loader.loadModel(sphere_path)
            sphere.setPos(LVecBase3f(pos[0], pos[1], pos[2]))
            sphere.setScale(0.005, 0.005, 0.005)
            sphere.setColor(1, 0, 0)
            sphere.reparentTo(self.feature_point_parent_node)

    def save_colored_pc(self):
        file = tkinter.filedialog.asksaveasfile(mode='w', defaultextension='.ply')
        if file is None:
            return

        util.save_point_cloud(self.source_pc_node, file.name)


    def load(self, filepath):
        filepath = os.path.abspath(filepath)
        filepath = Filename.fromOsSpecific(filepath).getFullpath()

        if self.source_mesh_node is not None:
            self.source_mesh_node.removeNode()
        self.source_mesh_node = self.loader.loadModel(filepath).findAllMatches('**/+GeomNode')[0]

        if self.source_pc_node is not None:
            self.source_pc_node.removeNode()
        self.source_pc_node = util.mesh_node_to_point_cloud_node(self.source_mesh_node)
        self.source_pc_node.reparentTo(self.source_parent_node)

        self.camPivot.setPos(self.source_pc_node.getBounds().getCenter())


    def setCamera(self):
        """ Define camera parameters """
        lens = self.defaultLens()
        # Camera step for changes
        self.camSpeed = .05
        self.camZoomStep = .3

        # Camera
        self.cam = Camera("cam5")
        self.cam.setLens(lens)
        self.camera = self.render.attachNewNode(self.cam)
        self.camPivot = self.render.attachNewNode("cam_pivot")
        self.camera.reparent_to(self.camPivot)
        self.camera.set_y(-2)

        # Setup each camera.
        self.view.setCamera(self.camera)

        """Disable the mouse and set up mouse-view functions"""
        self.disableMouse()

        # Set up camera zoom
        self.accept('wheel_up', self.zoom_in)
        self.accept('wheel_down', self.zoom_out)

        # Set up camera rotation
        self.accept('mouse1', self.wheel_down)
        self.accept('mouse1-up', self.wheel_up)
        self.lastMousePos = None
        self.wheel_pressed = False
        self.taskMgr.add(self.rotate_view, 'Rotate Camera View', extraArgs=[], appendTask=True)


    def defaultLens(self):
        # Camera angles
        lens = PerspectiveLens()
        camHorAng = 40
        camVerAng = 30
        lens.setFov(camHorAng, camVerAng)

        # Near/Far plane
        camNear = 0.01
        lens.setNear(camNear)
        camFar = 5
        lens.setFar(camFar)

        return lens


    def setLight(self):
        light = PointLight('Light')
        light.set_color((1, 1, 1, 1))
        light = self.render.attachNewNode(light)
        light.reparentTo(self.render)
        light.setPos(-1, -1, -1)
        self.render.setLight(light)

        light = PointLight('Light')
        light.set_color((1, 1, 1, 1))
        light = self.render.attachNewNode(light)
        light.reparentTo(self.render)
        light.setPos(1, 1, 1)
        self.render.setLight(light)


    # Functions for camera zoom
    def zoom_out(self):
        """Translate the camera along the y axis of its matrix to zoom out the view"""
        self.view_changed = True
        self.camera.setPos(self.camera.getMat().xform((0, -self.camZoomStep, 0, 1)).getXyz())


    def zoom_in(self):
        """Translate the camera along the y axis its matrix to zoom in the view"""
        self.view_changed = True
        newCamPos = self.camera.getMat().xform((0, self.camZoomStep, 0, 1)).getXyz()
        self.camera.setPos(newCamPos)


    # Functions for camera rotation
    def wheel_down(self):
        self.wheel_pressed = True
        self.lastMousePos = None


    def wheel_up(self):
        self.wheel_pressed = False
        self.lastMousePos = None


    def rotate_view(self, task):
        if self.wheel_pressed and self.mouseWatcherNode.hasMouse():
            mouse_pos = self.mouseWatcherNode.getMouse()
            if self.lastMousePos is None:
                self.lastMousePos = Point2(mouse_pos)
            else:
                d_heading, d_pitch = (mouse_pos - self.lastMousePos) * 100.
                pivot = self.camPivot
                pivot.set_hpr(pivot.get_h() - d_heading, pivot.get_p() + d_pitch, 0.)
                self.view_changed = True
                self.lastMousePos = Point2(mouse_pos)
        return task.again


app = App()
app.run()