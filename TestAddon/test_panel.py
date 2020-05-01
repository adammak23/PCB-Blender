import bpy

from bpy.props import StringProperty, FloatProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from . Test import GeneratePCB

def FilePath(_name, _description="", _default=""):
    return StringProperty(name=_name, default = _default, description=_description, subtype = 'FILE_PATH')
    
def Float(_name, _description="", _default=""):
    return FloatProperty(name=_name, default = _default, description=_description)

class LayoutDemoPanel(Panel, ImportHelper):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Layout Demo"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    bpy.types.Scene.first_path = FilePath("Gerber folder", "Define file path to gerber folder")
    bpy.types.Scene.second_path = FilePath("Output folder", "Define output file path")
    bpy.types.Scene.width = Float("Width","Max image resolution [Width]",1024)
    bpy.types.Scene.height = Float("Height","Max image resolution [Height]",1024)

    def draw(self, context):
        layout = self.layout
        split = layout.split()
        col = layout.column()
        row = layout.row()

        first_string = col.prop(context.scene, 'first_path')
        second_string = col.prop(context.scene, 'second_path')
        width = row.prop(context.scene, 'width')
        height = row.prop(context.scene, 'height')

        #col = split.column()
        #col = layout.column()

        # first_string = col.prop(context.scene, 'first_path')
        # second_string = col.prop(context.scene, 'second_path')

        # col = split.column()
        # col = split.column()
        # width = col.prop(context.scene, 'width')
        


        row = layout.row()
        
        GeneratePCB.GERBER_FOLDER = bpy.context.scene.first_path
        GeneratePCB.OUTPUT_FOLDER = bpy.context.scene.second_path
        GeneratePCB.width_resolution = bpy.context.scene.width
        GeneratePCB.height_resolution = bpy.context.scene.height
        row.operator('test.generate')
        