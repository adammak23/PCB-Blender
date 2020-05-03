import bpy

from bpy.props import StringProperty, FloatProperty, EnumProperty, BoolProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from . Test import GeneratePCB

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

    bpy.types.Scene.gerber_folder = FilePath("Gerber folder", "Define file path to gerber folder")
    bpy.types.Scene.output_path = FilePath("Output folder", "Define output file path, images will be saved there")
    bpy.types.Scene.width = Float("Width","Max image resolution [Width]",1024)
    bpy.types.Scene.height = Float("Height","Max image resolution [Height]",1024)
    bpy.types.Scene.expand = bpy.props.BoolProperty(default=False)

    bpy.types.Scene.cu = FilePath("Copper Up", "Define file")
    bpy.types.Scene.mu = FilePath("Mask Up", "Define file")
    bpy.types.Scene.pu = FilePath("Paste Up", "Define file")
    bpy.types.Scene.su = FilePath("Silk Up", "Define file")

    bpy.types.Scene.cb = FilePath("Copper Bottom", "Define file")
    bpy.types.Scene.mb = FilePath("Mask Bottom", "Define file")
    bpy.types.Scene.pb = FilePath("Paste Bottom", "Define file")
    bpy.types.Scene.sb = FilePath("Silk Bottom", "Define file")

    bpy.types.Scene.edg = FilePath("Edge cut/outline", "Define file")
    bpy.types.Scene.drl = FilePath("Drill", "Define file")
    bpy.types.Scene.drl2 = FilePath("Secondary Drill", "Define file")

    def draw(self, context):

        layout = self.layout
        split = layout.split()
        col = layout.column()
        row = layout.row()

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

        col = layout.column()
        row = layout.row()
        row.label(text="Max render resolution:")
        row.prop(context.scene, 'width')
        row.prop(context.scene, 'height')

        col = layout.column()
        col.prop(context.scene, 'output_path')


        #col = split.column()
        #col = layout.column()

        # first_string = col.prop(context.scene, 'gerber_folder')
        # second_string = col.prop(context.scene, 'output_path')

        # col = split.column()
        # col = split.column()
        # width = col.prop(context.scene, 'width')
        
        
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
        row.operator('pcb.generate')
