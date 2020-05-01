import bpy

from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from . Test import GeneratePCB

def FilePath(_name, _description="", _default=""):
    return StringProperty(name=_name, default = _default, description=_description, subtype = 'FILE_PATH')
    

class LayoutDemoPanel(Panel, ImportHelper):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Layout Demo"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    bpy.types.Scene.first_path = FilePath("Gerber folder", "Define file path to gerber folder")
    bpy.types.Scene.second_path = FilePath("Output folder", "Define output file path")
    bpy.types.Scene.width = FilePath("namexd","xd","description xd")

    def draw(self, context):
        layout = self.layout
        
        col = layout.column()
        first_string = col.prop(context.scene, 'first_path')
        second_string = col.prop(context.scene, 'second_path')
        width = col.prop(context.scene, 'width')
        
        row = layout.row()
        #GenerateOperator.string1 = bpy.context.scene.first_path
        #row.operator('xd.generate')
        
        GeneratePCB.GERBER_FOLDER = bpy.context.scene.first_path
        GeneratePCB.OUTPUT_FOLDER = bpy.context.scene.second_path
        row.operator('test.generate')
        