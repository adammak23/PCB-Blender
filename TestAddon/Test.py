import os
from gerber import PCB
from bpy.types import Operator

class GeneratePCB(Operator):
    bl_idname = "lol.generate"
    bl_label = "GENEREJT"
    string1 = ""
    string2 = ""

    def execute(self, context):
        GERBER_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'gerbers'))
        # Create a new PCB instance
        pcb = PCB.from_directory(GERBER_FOLDER)

        for layer in pcb.layers:
            print(layer)
            print('bounds: ',layer.bounds)
            print(layer.primitives)

        return {'FINISHED'}

