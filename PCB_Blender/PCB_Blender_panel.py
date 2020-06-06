import bpy

from bpy.props import StringProperty, FloatProperty, EnumProperty, BoolProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from . PCB_Blender import PCB_Generate

def FilePath(_name, _description="", _default=""):
    return StringProperty(name=_name, default = _default, description=_description, subtype = 'FILE_PATH')
    
def Float(_name, _description="", _default=""):
    return FloatProperty(name=_name, default = _default, description=_description)

class PCB_LayoutPanel(Panel, ImportHelper):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "PCB Renderer"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    scene = bpy.types.Scene
    scene.gerber_folder = FilePath("", "Define file path to gerber folder")
    scene.output_path = FilePath("Output folder", "Define output file path, PCB images will be saved there")
    scene.width = Float("Width","Max image resolution [Width]", 1024)
    scene.height = Float("Height","Max image resolution [Height]", 1024)
    scene.expand = bpy.props.BoolProperty(default=False)
    scene.model_folder = FilePath("", "Define file path to Your own models library")

    scene.cu = FilePath("Copper Top", "Define file")
    scene.mu = FilePath("Mask Top", "Define file")
    scene.pu = FilePath("Paste Top", "Define file")
    scene.su = FilePath("Silk Top", "Define file")

    scene.cb = FilePath("Copper Bottom", "Define file")
    scene.mb = FilePath("Mask Bottom", "Define file")
    scene.pb = FilePath("Paste Bottom", "Define file")
    scene.sb = FilePath("Silk Bottom", "Define file")

    scene.edg = FilePath("Edge cut/outline", "Define file")
    scene.drl = FilePath("Drill", "Define file")
    scene.drl2 = FilePath("Secondary Drill", "Define file")

    scene.placeTop = FilePath("", "Define file")
    scene.placeBottom = FilePath("", "Define file")

    Program = [
        ("KICAD", "KiCad", "Make sure you downloaded models and placed them in this addon folder\models\KICAD", 1),
        ("GEDA", "gEDA", "Make sure you downloaded models and placed them in this addon folder\models\GEDA", 2),
        ("AUTO", "Auto Detect", "Make sure you downloaded models and placed them in this addon folder\models", "TIME", 3),
        ("SELF", "Select folder", "Select my own models library folder (only .blend files are supported!)","PACKAGE", 4)
        ]
    scene.PickAndPlaceProgram = EnumProperty(name = "", description = "Program which generated Pick and Place file", items = Program, default = "SELF")

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
        col.label(text="Models database")
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
        
        PCB_Generate.width_resolution = bpy.context.scene.width
        PCB_Generate.height_resolution = bpy.context.scene.height
        PCB_Generate.GERBER_FOLDER = bpy.context.scene.gerber_folder
        PCB_Generate.OUTPUT_FOLDER = bpy.context.scene.output_path

        PCB_Generate.use_separate_files = bpy.context.scene.expand
        PCB_Generate.cu  = bpy.context.scene.cu
        PCB_Generate.mu  = bpy.context.scene.mu
        PCB_Generate.pu  = bpy.context.scene.pu
        PCB_Generate.su  = bpy.context.scene.su
        PCB_Generate.cb  = bpy.context.scene.cb
        PCB_Generate.mb  = bpy.context.scene.mb
        PCB_Generate.pb  = bpy.context.scene.pb
        PCB_Generate.sb  = bpy.context.scene.sb

        PCB_Generate.edg = bpy.context.scene.edg
        PCB_Generate.drl = bpy.context.scene.drl
        PCB_Generate.drl2 = bpy.context.scene.drl2

        PCB_Generate.placeTop = bpy.context.scene.placeTop
        PCB_Generate.placeBottom = bpy.context.scene.placeBottom
        PCB_Generate.placeProgram = bpy.context.scene.PickAndPlaceProgram
        PCB_Generate.model_folder = bpy.context.scene.model_folder

        row.operator('pcb.generate', icon = 'SYSTEM')
