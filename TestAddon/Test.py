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
    CircleResolution = 4
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

def CairoExample_FilesIntoLayers(GERBER_FOLDER, OUTPUT_FOLDER):
   
    from .gerber import load_layer
    from .gerber.render import RenderSettings, theme
    from .gerber.render.cairo_backend import GerberCairoContext
    # Open the gerber files
    copper = load_layer(os.path.join(GERBER_FOLDER, 'copper.GTL'))
    mask = load_layer(os.path.join(GERBER_FOLDER, 'soldermask.GTS'))
    silk = load_layer(os.path.join(GERBER_FOLDER, 'silkscreen.GTO'))
    drill = load_layer(os.path.join(GERBER_FOLDER, 'ncdrill.DRD'))

    # Create a new drawing context
    ctx = GerberCairoContext()

    # Draw the copper layer. render_layer() uses the default color scheme for the
    # layer, based on the layer type. Copper layers are rendered as
    ctx.render_layer(copper)

    # Draw the soldermask layer
    ctx.render_layer(mask)


    # The default style can be overridden by passing a RenderSettings instance to
    # render_layer().
    # First, create a settings object:
    our_settings = RenderSettings(color=theme.COLORS['white'], alpha=0.85)

    # Draw the silkscreen layer, and specify the rendering settings to use
    ctx.render_layer(silk, settings=our_settings)

    # Draw the drill layer
    ctx.render_layer(drill)

    # Write output to png file
    #ctx.dump(os.path.join(os.path.dirname(__file__), 'cairo_example.png'))
    ctx.dump(os.path.join(OUTPUT_FOLDER, 'cairo_example.png'))

    # Load the bottom layers
    copper = load_layer(os.path.join(GERBER_FOLDER, 'bottom_copper.GBL'))
    mask = load_layer(os.path.join(GERBER_FOLDER, 'bottom_mask.GBS'))

    # Clear the drawing
    ctx.clear()

    # Render bottom layers
    ctx.render_layer(copper)
    ctx.render_layer(mask)
    ctx.render_layer(drill)

    # Write png file
    #ctx.dump(os.path.join(os.path.dirname(__file__), 'cairo_bottom.png'))
    ctx.dump(os.path.join(OUTPUT_FOLDER, 'cairo_bottom.png'))

def TestRender(GERBER_FOLDER, OUTPUT_FOLDER):

    from .gerber import PCB
    from .gerber.render import theme
    from .gerber.render.cairo_backend import GerberCairoContext


    GERBER_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'gerbers'))


    # Create a new drawing context
    ctx = GerberCairoContext()

    # Create a new PCB instance
    pcb = PCB.from_directory(GERBER_FOLDER)

    # Render PCB top view
    ctx.render_layers(pcb.top_layers,
                    os.path.join(OUTPUT_FOLDER, 'pcb_top.png',),
                    theme.THEMES['Blue'], max_width=2048, max_height=2048)

    # # Render PCB bottom view
    # ctx.render_layers(pcb.bottom_layers,
    #                 os.path.join(OUTPUT_FOLDER, 'pcb_bottom.png'),
    #                 theme.THEMES['default'], max_width=2048, max_height=2048)

    # # Render copper layers only
    # ctx.render_layers(pcb.copper_layers + pcb.drill_layers,
    #                 os.path.join(OUTPUT_FOLDER,
    #                             'pcb_transparent_copper.png'),
    #                 theme.THEMES['Transparent Multilayer'], max_width=2048, max_height=2048)


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
    OUTPUT_FOLDER = ""

    def execute(self, context):

        ### NEW WAY TESTING ########################################

        if(self.GERBER_FOLDER == ""):
            ShowMessageBox("Please enter path to folder with gerber files", "Error", 'ERROR')
            return

        if(self.OUTPUT_FOLDER == ""):
            ShowMessageBox("Please enter path to output folder", "Error", 'ERROR')
            return

        TestRender(self.GERBER_FOLDER, self.OUTPUT_FOLDER)

        return {'FINISHED'}
