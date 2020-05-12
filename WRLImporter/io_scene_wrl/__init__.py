# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>

bl_info = {
    "name": "WRL format",
    "author": "Campbell Barton, Bart, Bastien Montagne, Seva Alekseyev, Adam Makiewicz",
    "version": (2, 3, 0),
    "blender": (2, 82),
    "location": "File > Import",
    "description": "Import WRL, this is modified implementation of x3d/vrml2 importer",
    "warning": "THIS IS BETA VERSION",
    "category": "Import-Export",
    "support": "TESTING",
    "wiki_url": "https://github.com/adammak23/FreePCB-Blender",
}

import bpy
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        orientation_helper,
        axis_conversion,
        path_reference_mode,
        )

@orientation_helper(axis_forward='Y', axis_up='Z')
class ImportWRL(bpy.types.Operator, ImportHelper):
    """Import an WRL file"""
    bl_idname = "import_scene.wrl"
    bl_label = "Import WRL"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".wrl"
    filter_glob: StringProperty(default="*.wrl", options={'HIDDEN'})

    def execute(self, context):
        from . import import_wrl

        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            ))
        global_matrix = axis_conversion(from_forward=self.axis_forward,
                                        from_up=self.axis_up,
                                        ).to_4x4()
        keywords["global_matrix"] = global_matrix
        
        return import_wrl.load(context, **keywords)

    def draw(self, context):
        pass


class WRL_PT_import_transform(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_wrl"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "axis_forward")
        layout.prop(operator, "axis_up")


def menu_func_import(self, context):
    self.layout.operator(ImportWRL.bl_idname,
                         text="WRL Extensible 3D (.vrml2/.wrl)")

classes = (
    ImportWRL,
    WRL_PT_import_transform,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()