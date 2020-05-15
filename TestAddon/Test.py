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

# TODO: Saving timestamp in filename
#from datetime import datetime

# Cairo rendering
from .gerber import load_layer
from .gerber.render import RenderSettings, theme
from .gerber.render.cairo_backend import GerberCairoContext

# Placement reading
import csv

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

def CairoExample_FilesIntoLayers(GERBER_FOLDER, OUTPUT_FOLDER):
   
    from .gerber import load_layer
    from .gerber.render import RenderSettings, theme
    from .gerber.render.cairo_backend import GerberCairoContext
    # Open the gerber files
    copper = load_layer(os.path.join(GERBER_FOLDER, 'proste1-F_Cu.gbr'))
    mask = load_layer(os.path.join(GERBER_FOLDER, 'proste1-F_Mask.gbr'))
    paste = load_layer(os.path.join(GERBER_FOLDER, 'proste1-F_Paste.gbr'))
    silk = load_layer(os.path.join(GERBER_FOLDER, 'proste1-F_SilkS.gbr'))
    drill = load_layer(os.path.join(GERBER_FOLDER, 'proste1-PTH.drl'))
    outline = load_layer(os.path.join(GERBER_FOLDER, 'proste1-Edge_Cuts.gbr'))

    # Create a new drawing context
    ctx = GerberCairoContext()

    ctx.render_layer(outline)

    # Draw the copper layer. render_layer() uses the default color scheme for the
    # layer, based on the layer type. Copper layers are rendered as
    ctx.render_layer(copper)

    ctx.render_layer(paste)
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
    ctx.dump(os.path.join(OUTPUT_FOLDER, 'cairo_example2.png'))

    # # Load the bottom layers
    # copper = load_layer(os.path.join(GERBER_FOLDER, 'bottom_copper.GBL'))
    # mask = load_layer(os.path.join(GERBER_FOLDER, 'bottom_mask.GBS'))

    # # Clear the drawing
    # ctx.clear()

    # # Render bottom layers
    # ctx.render_layer(copper)
    # ctx.render_layer(mask)
    # ctx.render_layer(drill)

    # # Write png file
    # #ctx.dump(os.path.join(os.path.dirname(__file__), 'cairo_bottom.png'))
    # ctx.dump(os.path.join(OUTPUT_FOLDER, 'cairo_bottom.png'))

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

def mil_to_meters(input):
    # mil = 1/1000 cal
    # 100 mils = 2.54 mm
    # 1 mil = 0.0254 mm = 0.0000254 m
    return float(float(input)*0.0000254)

def mm_to_meters(input):
    return float(float(input)*0.001)

### Test functions above

def deselectAll():
    bpy.ops.object.select_all(action='DESELECT')

def read_csv(file_csv, program = 'AUTO'):
    
    objects = None

    directory = 'testmodels'+os.sep
    if program == 'AUTO':
        pass
    else:
        directory = directory + program + os.sep

    component_root = os.path.abspath(os.path.dirname(directory))

    with open(file_csv, newline='', encoding='ISO-8859-15') as fobj:
        reader = csv.reader(filter(lambda row: row[0] != '#', fobj))
        layout_table = list(reader)

    required = list(col[2] for col in layout_table)

    compfiles = []

    import glob
    for root, dirs, files in os.walk(component_root):
        for f in files:
            if f.lower().endswith('.blend'):
                compfiles.append((root + os.sep + f))

    for compfile in compfiles:
        #print("Loading models from " + compfile + "\n")
        with bpy.data.libraries.load(compfile, link=True) as (data_from, data_to):
            #for value in data_from.meshes:
            #    print(value)
            found = [value for value in data_from.meshes if value in required]
            for f in found:
                print("    Found: " + f + "\n")
            data_to.meshes = found
            required = [value for value in required if value not in data_from.meshes]
            
    print("\nMissing components:\n")
    for missing in required:
        print("    " + missing + "\n")
            
    objects_data  = bpy.data.objects
    objects_scene = bpy.context.scene.objects

    deselectAll()

    objects = []

    for id, name, value, x, y, rot, side in layout_table:

        if id == "(unknown)" or id == "Ref":
            continue
        z = 0
        yrot = 0
        if side == "bottom":
            z = -1.6
            yrot = 180 / 57.2957795
        loc = tuple(float(val)/100 for val in (x, y, z))
        frot = float(rot)
        try:
            if rotations[id]:
                frot = rotations[id]
        except:
            pass
        try:
            if self.dnp[id] == 1:
                continue
        except:
            pass
        frot = frot / 57.2957795
        zrot = tuple(float(val) for val in (0, yrot, frot))

        oname = id + " - " + name
        for ob in bpy.data.objects:
            if ob.name.startswith(id + " - "):
                bpy.context.view_layer.objects.active = ob
                ob.select_set(True)
                bpy.ops.object.delete()
        
        mesh = bpy.data.meshes.get(value)
        dupli = objects_data.new(oname, mesh)
        dupli.location = loc
        dupli.rotation_euler = zrot
        bpy.context.scene.collection.objects.link(dupli)
        
        objects.append(oname)

# Blender UI context

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

        def draw(self, context):
            self.layout.label(text=message)

        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def ChangeArea(area_type, space_type):
    for area in bpy.context.screen.areas: 
        if area.type == area_type:
            space = area.spaces.active
            if space.type == area_type:
                space.shading.type = space_type

# Utils

def MoveUp(obj, times=1, distance = 0.0001):
    if obj is None: return
    for x in range(times):
        obj.location += mathutils.Vector((0,0,distance))

def MoveDown(obj, times=1, distance = 0.0001):
    MoveUp(obj, times, -distance)

# Generating Functions:

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

    TempObj.select_set(True)
    bpy.context.view_layer.objects.active = TempObj

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.cube_project(cube_size=1, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    return TempObj

def RenderOutline(name, layer, material, offset, scaler):
    if layer is None: return

    mesh_i = 0
    mesh_verts = []
    mesh_edges = []
    mesh_faces = []

    for primitive in layer.primitives:

        if(type(primitive) == gerber.primitives.Line):
            
            if offset is None:
                vec1 = [(primitive.start[0])/scaler[0], (primitive.start[1])/scaler[1],0]
            else:
                vec1 = [(primitive.start[0] + offset[0])/scaler[0], (primitive.start[1] + offset[1])/scaler[1],0]
            mesh_verts.append(vec1)
            mesh_i+=1

    me = bpy.data.meshes.new("outline")
    me.materials.append(material)
    me.from_pydata(mesh_verts, mesh_edges, mesh_faces)
    me.validate()
    me.update()
    MeshObj = bpy.data.objects.new("outline", me)
    bpy.context.scene.collection.objects.link(MeshObj)

    MeshObj.select_set(True)
    bpy.context.view_layer.objects.active = MeshObj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.edge_face_add()
    bpy.ops.uv.cube_project(cube_size=1, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return MeshObj

def CreateModel(name, source_folder, ctx, pcb_instance=None):

    mat = bpy.data.materials.new(name = name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texImage.image = bpy.data.images.load(os.path.join(source_folder, name+'.png'))
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

    mesh = None
    if(pcb_instance is not None):
        if(pcb_instance.outline_layer is not None):
            mesh = RenderOutline(
                "outline",
                pcb_instance.outline_layer,
                mat,
                None, #-mathutils.Vector((ctx.origin_in_inch[0], ctx.origin_in_inch[1], 0))
                mathutils.Vector((100, 100, 0)))
        else:
            mesh = RenderBounds(
                    "outline",
                    ctx.first_bounds,
                    mat,
                    )
    return mesh

def ReadPlacement(top,bottom=None):
    with open(top, newline='') as csvfile:
        placement = csv.reader(csvfile, delimiter=' ', quotechar='|')
        for row in placement:
            print(', '.join(row))

    return {'FINISHED'}

# Cairo-based rendering

def CreateImage(name, layers, ctx, GERBER_FOLDER, OUTPUT_FOLDER, w=512, h=512, pcb_instance=None):
     
    layers_to_render = layers
    if(pcb_instance is not None):
        if pcb_instance.outline_layer is not None:
            layers_to_render.insert(0, pcb_instance.outline_layer)

    ctx.render_layers(layers_to_render, os.path.join(OUTPUT_FOLDER, name+'.png'), theme.THEMES['default'], max_width=w, max_height=h)

class GeneratePCB(Operator):
    bl_idname = "pcb.generate"
    bl_label = "Render"
    bl_description = "Warning: Files in Output folder might be overriden"
    GERBER_FOLDER = ""
    OUTPUT_FOLDER = ""
    width_resolution = 1024
    height_resolution = 1024

    use_separate_files = False
    cu = None
    mu = None
    pu = None
    su = None
    cb = None
    mb = None
    pb = None
    sb = None
    edg = None
    drl = None
    drl2 = None
    placeTop = None
    placeBottom = None
    placeProgram = None

    def execute(self, context):

        read_csv(self.placeTop, self.placeProgram)
        return {'CANCELLED'}

        if(str(self.OUTPUT_FOLDER) == ""):
            ShowMessageBox("Please enter path to output folder", "Error", 'ERROR')
            return {'CANCELLED'}

        if(self.use_separate_files is not None):
            if(self.use_separate_files):
                # Create a new drawing context
                ctx = GerberCairoContext()
                # Preprocess and load layers from strings
                string_up_layers     = [self.edg, self.pu, self.su, self.cu, self.mu, self.drl, self.drl2]
                up_layers = []
                string_bottom_layers = [self.edg, self.pb, self.sb, self.cb, self.mb, self.drl, self.drl2]
                bottom_layers = []
                for stringlayer in string_up_layers:
                    if(stringlayer is not None and stringlayer is not ""):
                        up_layers.append(load_layer(os.path.join(self.GERBER_FOLDER, stringlayer)))
                for stringlayer in string_bottom_layers:
                    if(stringlayer is not None and stringlayer is not ""):
                        bottom_layers.append(load_layer(os.path.join(self.GERBER_FOLDER, stringlayer)))

                # Render images
                CreateImage("Top_layer", up_layers, ctx, self.GERBER_FOLDER, self.OUTPUT_FOLDER, self.width_resolution, self.height_resolution)
                CreateImage("Bottom_layer", bottom_layers, ctx, self.GERBER_FOLDER, self.OUTPUT_FOLDER, self.width_resolution, self.height_resolution)

                # Create models
                Top_layer = CreateModel("Top_layer", self.OUTPUT_FOLDER, ctx)
                MoveUp(Top_layer)
                Bottom_layer = CreateModel("Bottom_layer", self.OUTPUT_FOLDER, ctx)
                MoveDown(Bottom_layer)
                
                # Placement list

                ChangeArea('VIEW_3D', 'MATERIAL')
                return {'FINISHED'}


        if(str(self.GERBER_FOLDER) == ""):
            ShowMessageBox("Please enter path to folder with gerber files", "Error", 'ERROR')
            return {'CANCELLED'}
        else:
            # Create a new drawing context
            ctx = GerberCairoContext()
            # Create a new PCB instance
            pcb = PCB.from_directory(self.GERBER_FOLDER)
            # Render images
            CreateImage("Top_layer", pcb.top_layers, ctx, self.GERBER_FOLDER, self.OUTPUT_FOLDER, self.width_resolution, self.height_resolution, pcb_instance = pcb)
            CreateImage("Bottom_layer", pcb.bottom_layers, ctx, self.GERBER_FOLDER, self.OUTPUT_FOLDER, self.width_resolution, self.height_resolution, pcb_instance = pcb)

            # Create models
            Top_layer = CreateModel("Top_layer", self.OUTPUT_FOLDER, ctx, pcb_instance = pcb)
            MoveUp(Top_layer)
            Bottom_layer = CreateModel("Bottom_layer", self.OUTPUT_FOLDER, ctx, pcb_instance = pcb)
            MoveDown(Bottom_layer)

            # Placement list
            #ReadPlacement(self.PlaceTop, self.placeBottom)

            ChangeArea('VIEW_3D', 'MATERIAL')
            return {'FINISHED'}

        #ShowMessageBox("Some files might be overridden in folder: "+self.OUTPUT_FOLDER, "Warning", 'IMPORT')

        #Render(self.GERBER_FOLDER, self.OUTPUT_FOLDER, self.width_resolution, self.height_resolution)
        