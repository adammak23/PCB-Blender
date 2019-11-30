import bpy

from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from . PCB_Creator import GenerateOperator

class LayoutDemoPanel(Panel, ImportHelper):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Layout Demo"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

# filter not working!
#    filter_glob: StringProperty(
#        default='*.jpg;*.jpeg;*.png;*.tif;*.tiff;*.bmp',
#        options={'HIDDEN'},
#        maxlen=255,  # Max internal buffer length, longer would be clamped.
#    )

    bpy.types.Scene.first_path = StringProperty(
    name = "1st File path",
    default = "",
    description = "Define file path",
    subtype = 'FILE_PATH'
    )
    bpy.types.Scene.second_path = StringProperty(
    name = "2nd File path",
    default = "",
    description = "Define file path",
    subtype = 'FILE_PATH'
    )


    def draw(self, context):
        layout = self.layout

        scene = context.scene
        
        col = layout.column()
        first_string = col.prop(context.scene, 'first_path')
        fsecond_string = col.prop(context.scene, 'second_path')
        
        row = layout.row()
        GenerateOperator.string1 = bpy.context.scene.first_path
        GenerateOperator.string2 = bpy.context.scene.second_path
        row.operator('xd.generate')