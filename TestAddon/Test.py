import os
import sys
# Jak sprawić żeby blender/python widział folder gerber
#os.chdir()
from . import gerber
from .gerber import PCB
import bpy
import bmesh
from bpy.types import Operator

def create_Vertices (name, verts):
    # Create mesh and object
    me = bpy.data.meshes.new('Mesh')
    ob = bpy.data.objects.new(name, me)
    ob.show_name = True
    # Link object to scene
    bpy.context.scene.collection.objects.link(ob)
    me.from_pydata(verts, [], [])
    # Update mesh with new data
    me.update()
    return ob

class GeneratePCB(Operator):
    bl_idname = "lol.generate"
    bl_label = "test gerber"
    string1 = ""
    string2 = ""
    
    def execute(self, context):
        #bpy.ops.object.select_all(action='SELECT')
        #bpy.ops.object.delete(use_global=False)

        GERBER_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'gerbers'))
        # Create a new PCB instance
        pcb = PCB.from_directory(GERBER_FOLDER)

        layer = pcb.layers[0]
        print(layer)
        i = 0
        verts_raw = []
        edges_raw = []
        for primitive in layer.primitives:
            if(type(primitive) == gerber.primitives.Line):
                verts_raw.append([primitive.start[0],primitive.start[1],0])
                verts_raw.append([primitive.end[0],primitive.end[1],0])
                edges_raw.append([i,i+1])
                i+=2

        # verts = []
        # for v in verts_raw:
        #     verts.append(v[1:])

        # edges = []
        # for a, b in edges_raw:
        #     edges.append((int(a[1:]), int(b[1:])))

        me = bpy.data.meshes.new("")
        me.from_pydata(verts_raw, edges_raw, [])
        me.validate()
        me.update()

        obj = bpy.data.objects.new("objeeect", me)
        bpy.context.scene.collection.objects.link(obj)
        obj.convert(target='CURVE')
        #bpy.ops.object.convert(target='CURVE')

        #obj.convert(target='CURVE')
        #print(obj)
        #print(bpy.context.scene.collection.objects[0])
        #obj.convert(target='CURVE')
        # i = 0
        # for primitive in layer.primitives:
        #     i+=1
        #     if(i==100):
        #         break
        #     if(type(primitive) == gerber.primitives.Line):
        #         bpy.ops.object.empty_add(type='PLAIN_AXES', location=(primitive.start[0], primitive.start[0], 0))
        #         bpy.ops.object.empty_add(type='PLAIN_AXES', location=(primitive.start[1], primitive.start[1], 0))
        #         bpy.ops.object.empty_add(type='PLAIN_AXES', location=(primitive.end[0], primitive.end[0], 0))
        #         bpy.ops.object.empty_add(type='PLAIN_AXES', location=(primitive.end[1], primitive.end[1], 0))

        #bpy.ops.curve.primitive_nurbs_path_add(enter_editmode=False, location=(0, 0, 0))
        #bpy.ops.curve.vertex_add(location=(0, 0, 0))

        #for layer in pcb.layers:
        #    print(layer)
        #    print('bounds: ',layer.bounds)
        #    print(layer.primitives)

        return {'FINISHED'}