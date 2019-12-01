import bpy
import bpy_extras
import os
import re
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper

# mil = 1/1000 cal
# 100 mils = 2.54 mm

def mil_to_meters(input):
    return float(float(input)*0.0000254)

#bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, location=(0, 0, 0))


def read_something(self, context, filepath, requested_extension):
    
    filename, extension = os.path.splitext(filepath)
        
    if extension != requested_extension:
        self.report({'ERROR'},"Wrong file extension - expected {}".format(requested_extension))
        return {'CANCELLED'}
    else: 
        filepath = bpy.path.abspath(filepath)
        file = open(filepath, 'r', encoding='utf-8')
        file_linesplitted = file.read().splitlines()
        iterator = 0
        current_drill_size = None;
        drill_sizes = {}
        for line in file_linesplitted:
            if line[0] == 'T': # drill size format
                temp_drill = list(filter(None, re.split('C0.', line)))
                if(len(temp_drill) > 1): # saving new drill size (input example: T01C0.014)
                    drill_sizes[temp_drill[0]] = temp_drill[1]
                else: # setting drill size (input example: T01)
                    current_drill_size = drill_sizes.get(temp_drill[0])
            if line[0] == ';': continue # ignore comments
            if len(line)==14 and line[0]=='X': # coordinates
                # splits text by X and Y, removes empty list elements
                Vector2 = list(filter(None,re.split('[XY]', line)))
                    #iterator += 1
                    #if iterator==10: return {'CANCELLED'}
                #parse mils to meters
                bpy.ops.mesh.primitive_uv_sphere_add(radius=mil_to_meters(current_drill_size), enter_editmode=False, location=(int(Vector2[0])*0.0000254, int(Vector2[1])*0.0000254, 0))
            
#        data = f.read()
#        f.close()
#        print(data)

    #return {'FINISHED'}


class GenerateOperator(Operator):
    bl_idname = "xd.generate"
    bl_label = "GENEREJT"
    string1 = ""
    string2 = ""

    def execute(self, context):
        read_something(self, context, self.string1, ".drl")

        return {'FINISHED'}



#def register():
#    bpy.utils.register_class(LayoutDemoPanel)
#    bpy.utils.register_class(GenerateOperator)
    #os.system("python -m ensurepip")

#def unregister():
#    bpy.utils.unregister_class(LayoutDemoPanel)
#    bpy.utils.unregister_class(GenerateOperator)


#if __name__ == "__main__":
#    register()
    
    # test call
    #bpy.ops.test.open_filebrowser('INVOKE_DEFAULT')


