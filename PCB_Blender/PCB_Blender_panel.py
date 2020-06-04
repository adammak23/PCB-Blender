import bpy

from bpy.props import StringProperty, FloatProperty, EnumProperty, BoolProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from . PCB_Blender import GeneratePCB

def FilePath(_name, _description="", _default=""):
    return StringProperty(name=_name, default = _default, description=_description, subtype = 'FILE_PATH')
    
def Float(_name, _description="", _default=""):
    return FloatProperty(name=_name, default = _default, description=_description)

class LayoutDemoPanel(Panel, ImportHelper):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "PCB Renderer"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    bpy.types.Scene.gerber_folder = FilePath("", "Define file path to gerber folder")
    bpy.types.Scene.output_path = FilePath("Output folder", "Define output file path, PCB images will be saved there")
    bpy.types.Scene.width = Float("Width","Max image resolution [Width]", 1024)
    bpy.types.Scene.height = Float("Height","Max image resolution [Height]", 1024)
    bpy.types.Scene.expand = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.model_folder = FilePath("", "Define file path to Your own models library")

    bpy.types.Scene.cu = FilePath("Copper Top", "Define file")
    bpy.types.Scene.mu = FilePath("Mask Top", "Define file")
    bpy.types.Scene.pu = FilePath("Paste Top", "Define file")
    bpy.types.Scene.su = FilePath("Silk Top", "Define file")

    bpy.types.Scene.cb = FilePath("Copper Bottom", "Define file")
    bpy.types.Scene.mb = FilePath("Mask Bottom", "Define file")
    bpy.types.Scene.pb = FilePath("Paste Bottom", "Define file")
    bpy.types.Scene.sb = FilePath("Silk Bottom", "Define file")

    bpy.types.Scene.edg = FilePath("Edge cut/outline", "Define file")
    bpy.types.Scene.drl = FilePath("Drill", "Define file")
    bpy.types.Scene.drl2 = FilePath("Secondary Drill", "Define file")

    bpy.types.Scene.placeTop = FilePath("", "Define file")
    bpy.types.Scene.placeBottom = FilePath("", "Define file")

    Program = [
        ("KICAD", "KiCad", "", 1),
        ("GEDA", "gEDA", "", 2),
        ("AUTO", "Auto Detect", "This might take long time to generate", "TIME", 3),
        ("SELF", "Select folder", "Select my own models library folder (only .blend files are supported!)","PACKAGE", 4)
        ]
    bpy.types.Scene.PickAndPlaceProgram = EnumProperty(name = "", description = "Program which generated Pick and Place file", items = Program, default = "AUTO")

    def draw(self, context):

        layout = self.layout
        col = layout.split(factor=0.5)

        col.label(text="Gerber folder")
        col.prop(context.scene, 'gerber_folder')


        row = layout.row()
        row.prop(context.scene, "expand", icon="TRIA_DOWN" if bpy.context.scene.expand else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Or select individually specific files:")

        if bpy.context.scene.expand:
            col = layout.column()
            col.label(text="To use gerber folder, collapse this section!", icon='ERROR')

            col.prop(context.scene, 'cu')
            col.prop(context.scene, 'mu')
            col.prop(context.scene, 'pu')
            col.prop(context.scene, 'su')

            col.prop(context.scene, 'cb')
            col.prop(context.scene, 'mb')
            col.prop(context.scene, 'pb')
            col.prop(context.scene, 'sb')

            col.prop(context.scene, 'edg')
            col.prop(context.scene, 'drl')
            col.prop(context.scene, 'drl2')

        col = layout.split(factor=0.5)
        col.label(text="Top Placement (.csv)")
        col.prop(context.scene, 'placeTop')

        col = layout.split(factor=0.5)
        col.label(text="Bottom Placement (.csv)")
        col.prop(context.scene, 'placeBottom')

        col = layout.split(factor=0.5)
        col.label(text="Pick And Place Program")
        col.prop(context.scene, 'PickAndPlaceProgram')
        if bpy.context.scene.PickAndPlaceProgram == 'SELF':
            col = layout.column()
            col.prop(context.scene, 'model_folder')

        col = layout.column()
        row = layout.row()
        row.label(text="Max resolution:")
        row.prop(context.scene, 'width')
        row.prop(context.scene, 'height')

        col = layout.column()
        col.prop(context.scene, 'output_path')
        
        row = layout.row()
        if(bpy.context.scene.output_path is not ""):
            col.label(text="Some files might be overridden in folder: "+bpy.context.scene.output_path, icon='FILE_TICK')
        
        GeneratePCB.width_resolution = bpy.context.scene.width
        GeneratePCB.height_resolution = bpy.context.scene.height
        GeneratePCB.GERBER_FOLDER = bpy.context.scene.gerber_folder
        GeneratePCB.OUTPUT_FOLDER = bpy.context.scene.output_path

        GeneratePCB.use_separate_files = bpy.context.scene.expand
        GeneratePCB.cu  = bpy.context.scene.cu
        GeneratePCB.mu  = bpy.context.scene.mu
        GeneratePCB.pu  = bpy.context.scene.pu
        GeneratePCB.su  = bpy.context.scene.su
        GeneratePCB.cb  = bpy.context.scene.cb
        GeneratePCB.mb  = bpy.context.scene.mb
        GeneratePCB.pb  = bpy.context.scene.pb
        GeneratePCB.sb  = bpy.context.scene.sb

        GeneratePCB.edg = bpy.context.scene.edg
        GeneratePCB.drl = bpy.context.scene.drl
        GeneratePCB.drl2 = bpy.context.scene.drl2

        GeneratePCB.placeTop = bpy.context.scene.placeTop
        GeneratePCB.placeBottom = bpy.context.scene.placeBottom
        GeneratePCB.placeProgram = bpy.context.scene.PickAndPlaceProgram
        GeneratePCB.model_folder = bpy.context.scene.model_folder

        row.operator('pcb.generate', icon = 'SYSTEM')
