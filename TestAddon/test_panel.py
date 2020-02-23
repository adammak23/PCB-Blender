import bpy

from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from . Test import GeneratePCB

class LayoutDemoPanel(Panel, ImportHelper):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Layout Demo"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    bpy.types.Scene.first_path = StringProperty(
    name = "1st File path",
    default = "",
    description = "Define file path",
    subtype = 'FILE_PATH'
    )

    def draw(self, context):
        layout = self.layout
        
        col = layout.column()
        first_string = col.prop(context.scene, 'first_path')
        
        row = layout.row()
        #GenerateOperator.string1 = bpy.context.scene.first_path
        #row.operator('xd.generate')
        
        GeneratePCB.GERBER_FOLDER = bpy.context.scene.first_path
        row.operator('test.generate')
        