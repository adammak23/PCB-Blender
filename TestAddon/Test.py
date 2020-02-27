import os
import sys
import math
from pprint import pprint
from . import gerber
from .gerber import PCB
import bpy
import bmesh
import mathutils
from bpy.types import Operator
from bpy.props import StringProperty

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

        def draw(self, context):
            self.layout.label(text=message)

        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def RenderBounds(name, bounds, material):

    if bounds is None: return

    mesh_i = 0
    mesh_verts = []
    mesh_edges = []
    mesh_faces = []

    mesh_verts.append([bounds[0][0], bounds[1][0],0])
    mesh_verts.append([bounds[0][1], bounds[1][0],0])
    mesh_verts.append([bounds[0][1], bounds[1][1],0])
    mesh_verts.append([bounds[0][0], bounds[1][1],0])
    mesh_edges.append([mesh_i,mesh_i+1])
    mesh_edges.append([mesh_i+1,mesh_i+2])
    mesh_edges.append([mesh_i+2,mesh_i+3])
    mesh_edges.append([mesh_i+3,mesh_i])
    mesh_faces.append([mesh_i,mesh_i+1,mesh_i+2])
    mesh_faces.append([mesh_i+2,mesh_i+3,mesh_i])

    me = bpy.data.meshes.new(name)
    me.materials.append(material)
    me.from_pydata(mesh_verts, mesh_edges, mesh_faces)
    me.validate()
    me.update()
    TempObj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(TempObj)
    return TempObj

def RenderCircle(self, mesh_i, mesh_verts, mesh_edges, mesh_faces, radius, Xax, Yax):
    # sin rotation is 2*PI = 6.283
    CircleResolution = 50
    first_point = mesh_i
    for x in range(CircleResolution):
        mesh_i+=1
        mesh_verts.append([radius*math.cos(x*(2*math.pi/CircleResolution))+Xax, radius*math.sin(x*(2*math.pi/CircleResolution))+Yax,0])
        if(x!=CircleResolution-1):
            mesh_edges.append([mesh_i-1,mesh_i])
            mesh_faces.append([mesh_i-1,mesh_i,first_point])
    mesh_edges.append([mesh_i-1,mesh_i-CircleResolution])
    # since in this function mesh_i is local immutable parameter we have to return it in order to change it's value
    return mesh_i

def RenderLayer(self, name, layer, material, optional_curve_thickness = 0.008):

    if layer is None: return

    mesh_i = 0
    mesh_verts = []
    mesh_edges = []
    mesh_faces = []

    curve_i = 0
    curve_verts = []
    curve_edges = []
    curve_thickness = 0.001

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
            mesh_i = RenderCircle(self, mesh_i, mesh_verts, mesh_edges, mesh_faces, primitive.radius, primitive._position[0], primitive._position[1])

        elif(type(primitive) == gerber.primitives.Line):
            curve_thickness = primitive.aperture.diameter
            #print(curve_thickness)
            if(curve_thickness > 0.05):
                mesh_i = RenderCircle(self, mesh_i, mesh_verts, mesh_edges, mesh_faces, curve_thickness/2, primitive.start[0], primitive.start[1])
                mesh_i = RenderCircle(self, mesh_i, mesh_verts, mesh_edges, mesh_faces, curve_thickness/2, (primitive.start[0]+primitive.end[0])/2, (primitive.start[1]+primitive.end[1])/2)
                mesh_i = RenderCircle(self, mesh_i, mesh_verts, mesh_edges, mesh_faces, curve_thickness/2, primitive.end[0], primitive.end[1])
            else:
                curve_verts.append([primitive.start[0],primitive.start[1],0])
                curve_verts.append([primitive.end[0],primitive.end[1],0])
                curve_edges.append([curve_i,curve_i+1])
                curve_i+=2
        #else (all other primitives are drills)

    me = bpy.data.meshes.new("mesh")
    me.materials.append(material)
    me.from_pydata(mesh_verts, mesh_edges, mesh_faces)
    me.validate()
    me.update()
    MeshObj = bpy.data.objects.new("mesh", me)
    bpy.context.scene.collection.objects.link(MeshObj)

    CurveObj = None
    if(curve_i > 0):
        cu = bpy.data.meshes.new("curve")
        cu.from_pydata(curve_verts, curve_edges, [])
        cu.validate()
        cu.update()
        CurveObj = bpy.data.objects.new("curve", cu)
        CurveObj.data.materials.append(material)
        bpy.context.scene.collection.objects.link(CurveObj)
        CurveObj.select_set(True)
        bpy.context.view_layer.objects.active = CurveObj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.convert(target='CURVE')
        CurveObj.data.dimensions = '2D'
        CurveObj.data.resolution_u = 1
        # TODO: sort all and add multiple objects, render separate with appropriate thickness
        # CurveObj.data.bevel_depth = curve_thickness/2
        # For now, simplified:
        CurveObj.data.bevel_depth = optional_curve_thickness
        CurveObj.data.bevel_resolution = 0

        bpy.ops.transform.resize(value=(1, 1, 0.01), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.ops.object.convert(target='MESH')
    
    if CurveObj and MeshObj:
        bpy.ops.object.select_all(action='DESELECT')
        CurveObj.select_set(True)
        MeshObj.select_set(True)
        bpy.ops.object.join()
        CurveObj.name = name
        bpy.ops.object.select_all(action='DESELECT')

        return CurveObj

    MeshObj.name = name
    return MeshObj

def MoveUp(obj, times=1, distance = 0.0001):
    if obj is None: return
    for x in range(times):
        obj.location += mathutils.Vector((0,0,distance))

def MoveDown(object, times=1, distance = 0.0001):
    MoveUp(object, times, -distance)

def BooleanCut(source, cutter):
    solidifymodifier = cutter.modifiers.new("SOLIDIFY", type = "SOLIDIFY")
    solidifymodifier.offset = 0
    bpy.context.view_layer.objects.active = cutter
    bpy.ops.object.modifier_apply(modifier="SOLIDIFY")
    
    boolmod = source.modifiers.new("BOOLEAN", type = "BOOLEAN")
    boolmod.object = cutter
    # boolmod.operation = 'DIFFERENCE' (is default)
    bpy.context.view_layer.objects.active = source
    bpy.ops.object.modifier_apply(modifier="BOOLEAN")
    bpy.data.objects.remove(cutter)

class GeneratePCB(Operator):
    bl_idname = "test.generate"
    bl_label = "test gerber"
    GERBER_FOLDER = ""
    string2 = ""

    def execute(self, context):
        #if(self.GERBER_FOLDER == ""):
        #    ShowMessageBox("Please enter path to folder with gerber files", "Error", 'ERROR')
        #    return

        #bpy.ops.object.select_all(action='SELECT')
        #bpy.ops.object.delete(use_global=False)

        MATERIALS = os.path.abspath(os.path.join(os.path.dirname(__file__), 'materials'))
        # Create a new PCB instance
        pcb = PCB.from_directory(self.GERBER_FOLDER)

        with bpy.data.libraries.load(MATERIALS+'/materials.blend', link=False) as (data_from, data_to):
            data_to.materials = data_from.materials

        #RenderLayer(self, pcb.layers[2].layer_class, pcb.layers[2], bpy.data.materials.get("Copper"))
        print(pcb.__format__)
        return {'FINISHED'}

        generated_layers = []

        Laminate = RenderBounds("Laminate", pcb.board_bounds, bpy.data.materials.get("Laminate"))
        Soldermask_Dark_Up = RenderBounds("Soldermask_Dark_Up", pcb.board_bounds, bpy.data.materials.get("Soldermask_Dark"))
        Soldermask_Dark_Down = RenderBounds("Soldermask_Dark_Down", pcb.board_bounds, bpy.data.materials.get("Soldermask_Dark"))

        # Can also make copy but then need to nake it single user and unlink data which makes it slower
        # Soldermask_Dark_Down = Soldermask_Dark_Up.copy()
        # bpy.context.scene.collection.objects.link(Soldermask_Dark_Down)

        MoveUp(Soldermask_Dark_Up, 1)
        MoveDown(Soldermask_Dark_Down, 1)
        
        for layer in pcb.copper_layers:
            if(layer in pcb.top_layers):
                generated_layers.append(layer)
                TopCopper = RenderLayer(self, "TopCopper", layer, bpy.data.materials.get("Copper"))
                MoveUp(TopCopper,2)
                Soldermask_Bright_Up = RenderLayer(self, "Soldermask_Bright_Up", layer, bpy.data.materials.get("Soldermask_Bright"))
                MoveUp(Soldermask_Bright_Up,3)
            else:
                generated_layers.append(layer)
                BottomCopper = RenderLayer(self, "BottomCopper", layer, bpy.data.materials.get("Copper"))
                MoveDown(BottomCopper,2)
                Soldermask_Bright_Down = RenderLayer(self, "Soldermask_Bright_Down", layer, bpy.data.materials.get("Soldermask_Bright"))
                MoveDown(Soldermask_Bright_Down,3)

        for layer in pcb.silk_layers:
            generated_layers.append(layer)
            if(layer.layer_class == 'topsilk'):
                Topsilk = RenderLayer(self, "Topsilk", layer, bpy.data.materials.get("White"), 0.001)
                Topsilk.name = "Topsilk"
                MoveUp(Topsilk, 4)
            else:
                Bottomsilk = RenderLayer(self, "Bottomsilk", layer, bpy.data.materials.get("White"), 0.001)
                Bottomsilk.name = "Bottomsilk"
                MoveDown(Bottomsilk, 4)

        # TODO: Simplify rendering so the top- and bottommask work well with Boolean Modifier (no intersecting geometry)
        TopMask = RenderLayer(self, "TopMask", pcb.topmask, bpy.data.materials.get("White"))
        BooleanCut(Soldermask_Bright_Up, TopMask)
        BottomMask = RenderLayer(self, "BottomMask", pcb.bottommask, bpy.data.materials.get("White"))
        BooleanCut(Soldermask_Bright_Down, BottomMask)


        # TODO: Drill layers

        return {'FINISHED'}
