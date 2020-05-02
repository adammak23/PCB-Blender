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

    gerber_folder = FilePath("Gerber folder", "Define file path to gerber folder")
    output_path = FilePath("Output folder", "Define output file path, images will be saved there")
    bpy.types.Scene.width = Float("Width","Max image resolution [Width]",1024)
    bpy.types.Scene.height = Float("Height","Max image resolution [Height]",1024)
    bpy.types.Scene.expand = bpy.props.BoolProperty(default=False)

    cu = FilePath("Copper Up", "Define file")
    mu = FilePath("Mask Up", "Define file")
    pu = FilePath("Paste Up", "Define file")
    su = FilePath("Silk Up", "Define file")

    cb = FilePath("Copper Bottom", "Define file")
    mb = FilePath("Mask Bottom", "Define file")
    pb = FilePath("Paste Bottom", "Define file")
    sb = FilePath("Silk Bottom", "Define file")

    edg = FilePath("Edge cut/outline", "Define file")
    drl = FilePath("Drill", "Define file")

    def draw(self, context):

        layout = self.layout
        split = layout.split()
        col = layout.column()
        row = layout.row()

        gf = col.prop(context.scene, 'gerber_folder')

        obj = context.scene
        row = layout.row()
        row.prop(obj, "expand", icon="TRIA_DOWN" if obj.expand else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Or select individually specific files:")

        if obj.expand:
            col = layout.column()
            col.label(text="To use gerber folder, collapse this section or clean fields below!", icon='ERROR')

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

        col = layout.column()
        row = layout.row()
        row.label(text="Max render resolution:")
        width = row.prop(context.scene, 'width')
        height = row.prop(context.scene, 'height')

        col = layout.column()
        second_string = col.prop(context.scene, 'output_path')


        #col = split.column()
        #col = layout.column()

        # first_string = col.prop(context.scene, 'gerber_folder')
        # second_string = col.prop(context.scene, 'output_path')

        # col = split.column()
        # col = split.column()
        # width = col.prop(context.scene, 'width')
        

        row = layout.row()
        
        GeneratePCB.width_resolution = bpy.context.scene.width
        GeneratePCB.height_resolution = bpy.context.scene.height
        GeneratePCB.GERBER_FOLDER = bpy.context.scene.gerber_folder
        GeneratePCB.OUTPUT_FOLDER = bpy.context.scene.output_path
        GeneratePCB.cu = bpy.types.Scene.cu
        GeneratePCB.mu = bpy.types.Scene.mu
        GeneratePCB.pu = bpy.types.Scene.pu
        GeneratePCB.su = bpy.types.Scene.su
        GeneratePCB.cb = bpy.types.Scene.cb
        GeneratePCB.mb = bpy.types.Scene.mb
        GeneratePCB.pb = bpy.types.Scene.pb
        GeneratePCB.sb = bpy.types.Scene.sb
        GeneratePCB.edg = bpy.types.Scene.edg
        GeneratePCB.drl = bpy.types.Scene.drl
        row.operator('pcb.generate')
