import os
import sys
import math
from pprint import pprint
# pprint(vars(your_object))
# How to make blender/python see gerber folder?
#os.chdir()
from . import gerber
from .gerber import PCB
import bpy
import bmesh
from bpy.types import Operator

# def create_Vertices (name, verts):
#     # Create mesh and object
#     me = bpy.data.meshes.new('Mesh')
#     ob = bpy.data.objects.new(name, me)
#     ob.show_name = True
#     # Link object to scene
#     bpy.context.scene.collection.objects.link(ob)
#     me.from_pydata(verts, [], [])
#     # Update mesh with new data
#     me.update()
#     return ob

def RenderLayer(self, layer):
    
    mesh_i = 0
    mesh_verts = []
    mesh_edges = []
    mesh_faces = []

    curve_i = 0
    curve_verts = []
    curve_edges = []
    curve_thickness = 0.001

    #pprint(vars(primitive))

    for primitive in layer.primitives:

        if(type(primitive) == gerber.primitives.Rectangle):
            mesh_verts.append([primitive.vertices[0][0],primitive.vertices[0][1],0])
            mesh_verts.append([primitive.vertices[1][0],primitive.vertices[1][1],0])
            mesh_verts.append([primitive.vertices[2][0],primitive.vertices[2][1],0])
            mesh_verts.append([primitive.vertices[3][0],primitive.vertices[3][1],0])
            mesh_edges.append([mesh_i,mesh_i+1])
            mesh_edges.append([mesh_i+1,mesh_i+2])
            mesh_edges.append([mesh_i+2,mesh_i+3])
            mesh_edges.append([mesh_i+3,mesh_i])
            mesh_faces.append([mesh_i,mesh_i+1,mesh_i+2])
            mesh_faces.append([mesh_i+2,mesh_i+3,mesh_i])
            mesh_i+=4

        elif(type(primitive) == gerber.primitives.Circle):
            r = primitive.radius
            # sin rotation is 2*PI = 6.283
            CircleResolution = 50
            first_point = mesh_i
            for x in range(CircleResolution):
                mesh_i+=1
                mesh_verts.append([r*math.cos(x*(2*math.pi/CircleResolution))+primitive._position[0], r*math.sin(x*(2*math.pi/CircleResolution))+primitive._position[1],0])
                if(x!=CircleResolution-1):
                    mesh_edges.append([mesh_i-1,mesh_i])
                    mesh_faces.append([mesh_i-1,mesh_i,first_point])
            mesh_edges.append([mesh_i-1,mesh_i-CircleResolution])

        elif(type(primitive) == gerber.primitives.Line):
            print(primitive.aperture.diameter)
            curve_thickness = primitive.aperture.diameter
            curve_verts.append([primitive.start[0],primitive.start[1],0])
            curve_verts.append([primitive.end[0],primitive.end[1],0])
            curve_edges.append([curve_i,curve_i+1])
            curve_i+=2

    me = bpy.data.meshes.new(str(layer)+"_Mesh")
    me.from_pydata(mesh_verts, mesh_edges, mesh_faces)
    me.validate()
    me.update()
    MeshObj = bpy.data.objects.new(str(layer)+"_Mesh", me)
    bpy.context.scene.collection.objects.link(MeshObj)

    if(curve_edges):
        cu = bpy.data.meshes.new(str(layer)+"_Curve")
        cu.from_pydata(curve_verts, curve_edges, [])
        cu.validate()
        cu.update()
        CurveObj = bpy.data.objects.new(str(layer)+"_Curve", cu)
        bpy.context.scene.collection.objects.link(CurveObj)
        CurveObj.select_set(True)
        bpy.context.view_layer.objects.active = CurveObj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.convert(target='CURVE')
        CurveObj.data.dimensions = '2D'
        CurveObj.data.resolution_u = 1
        CurveObj.data.bevel_depth = curve_thickness
        #CurveObj.data.data.splines[5].use_smooth = True


            #lps = obj.data.loops
            #bpy.context.view_layer.objects.active = obj
            #bpy.ops.object.select_all(action='SELECT')

            #area = bpy.context.area
            #old_area = bpy.context.area.type
            #area.type = 'VIEW_3D'
            #area.type = old_type
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

class GeneratePCB(Operator):
    bl_idname = "test.generate"
    bl_label = "test gerber"
    string1 = ""
    string2 = ""
    
    
    def execute(self, context):
        #bpy.ops.object.select_all(action='SELECT')
        #bpy.ops.object.delete(use_global=False)

        GERBER_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'gerbers'))
        # Create a new PCB instance
        pcb = PCB.from_directory(GERBER_FOLDER)

        RenderLayer(self, pcb.layers[0])
        #for layer in pcb.layers:
        #    RenderLayer(self, layer)
        return {'FINISHED'}
            #if(layer == 'topsilk'):