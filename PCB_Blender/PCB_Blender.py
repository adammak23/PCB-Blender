import os
import sys
import math

# Gerber reader
from . import gerber
from .gerber import PCB

# Blender core
import bpy
import bmesh
import mathutils
from bpy.types import Operator

# Saving timestamp in filename so they will not override in output folder
import time

# Cairo rendering
from .gerber import load_layer
from .gerber.render import RenderSettings, theme
from .gerber.render.cairo_backend import GerberCairoContext

# Placement reading
import csv

# Global variables:
units = 'metric'

# Reading Placement file

def ReadPlacement_csv(file_csv, program = 'SELF', folder = None):
    
    # For reading placement files
    objects = None

    directory = 'models'+os.sep
    if program == 'INTERNAL':
        pass
    elif program == 'SELF':
        directory = folder + os.sep

    component_root = os.path.abspath(os.path.dirname(directory))

    with open(file_csv, newline='', encoding='ISO-8859-15') as fobj:
        reader = csv.reader(filter(lambda row: row[0] != '#', fobj))
        layout_table = list(reader)

    # Truncate required names to 63 letters because it's max name length in Blender
    required = list((col[2])[:63] for col in layout_table)
    # Remove "Package" element from list, sometimes it's in description of columns in placement file (first row) 
    if 'Package' in required:
        required.remove('Package')
    compfiles = []

    # Recursively search folders in {addon folder}/models/ or models/{specified program folder}
    # for .blend files to append them
    import glob
    for root, dirs, files in os.walk(component_root):
        i = 0.0
        for f in files:
            UpdateProgress(i/len(files))
            i += 1.0
            
            if f.lower().endswith('.blend'):
                compfiles.append((root + os.sep + f))

    i = 0.0
    for compfile in compfiles:
        UpdateProgress(i/len(compfiles))
        i += 1.0
        # Loading models from .blends by mesh name
        # Later can be changed to scene object, for now models are single-mesh
        with bpy.data.libraries.load(compfile, link=True) as (data_from, data_to):
            found = [value for value in data_from.meshes if value in required]
            data_to.meshes = found
            required = [value for value in required if value not in data_from.meshes]

    #For each missing model try to find another with similar name (with most fitting keywords)
    #Every component is usually formed as follows: Type_(Subtype_)Dimensions_(AddiotionalDimensions_)(Rotation_)(AdditionalAttributes)
    separator = '_'
    for missing in required:
        separatedList = missing.split(separator)
        for compfile in compfiles:
            UpdateProgress(i/len(compfiles))
            found = False
            with bpy.data.libraries.load(compfile, link=True) as (data_from, data_to):
                i = 0
                # Search models with names starting with most keywords possible
                while i < len(separatedList)-1:
                    newSearch = separator.join(separatedList[:len(separatedList)-i])
                    newFound = [value for value in data_from.meshes if value.startswith(newSearch)]
                    if len(newFound) > 0:
                        elementFound = min(newFound, key=len)
                        requested  = separator.join(separatedList)
                        print("Found: ", elementFound, " similar to requested: ", requested)
                        data_to.meshes.append(elementFound)
                        for col in layout_table:
                            if col[2] == requested:
                                col[2] = elementFound
                        found = True
                        break
                    else:
                        i+=1
            if found:
                break
                
    objects_data  = bpy.data.objects
    objects_scene = bpy.context.scene.objects

    DeselectAll()

    objects = []

    scaler = 0.001
    if units == "metric":
        scaler = 0.001
    if units == "inch":
        scaler = 0.0254

    for id, name, value, x, y, rot, side in layout_table:

        if id == '(unknown)' or id == 'Ref':
            continue
        z = 0
        yrot = 0
        if side == 'bottom':
            z = -1.6
            yrot = 180 / 57.2957795
        loc = tuple(float(val) * scaler for val in (x, y, z))
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

        oname = id + ' - ' + name
        for ob in bpy.data.objects:
            if ob.name.startswith(id + ' - '):
                bpy.context.view_layer.objects.active = ob
                ob.select_set(True)
                bpy.ops.object.delete()
        
        mesh = bpy.data.meshes.get(value)
        dupli = objects_data.new(oname, mesh)
        dupli.location = loc
        dupli.rotation_euler = zrot
        dupli.scale = mathutils.Vector((0.00254,0.00254,0.00254))
        bpy.context.scene.collection.objects.link(dupli)
        
        objects.append(oname)

# Info Utilities

def RegisterProgress():
    bpy.context.window_manager.progress_begin(0, 1000)  

def UpdateProgress(num):
    bpy.context.window_manager.progress_update(num*10)

def EndProgress():
    bpy.context.window_manager.progress_end()

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

        def draw(self, context):
            self.layout.label(text=message)

        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

# Editor Utilities

def PurgeOrphanData():
    areaType = bpy.context.area.type
    bpy.context.area.type = 'OUTLINER'
    bpy.context.space_data.display_mode = 'ORPHAN_DATA'
    bpy.ops.outliner.orphans_purge()
    bpy.context.area.type = areaType

def DeselectAll():
    bpy.ops.object.select_all(action='DESELECT')

def ChangeArea(area_type, space_type):
    for area in bpy.context.screen.areas: 
        if area.type == area_type:
            space = area.spaces.active
            if space.type == area_type:
                space.shading.type = space_type

def ChangeClipping(amount):
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    s.clip_start = amount

## Move Utils

def Move(obj, distance = 0.0001):
    if obj is None: return
    obj.location += mathutils.Vector((0,0,distance))

# Mesh

def RenderBounds(name, bounds, scaler, material):
    if bounds is None: return
    print("Rendering Bounds")
    mesh_i = 0
    mesh_verts = []
    mesh_edges = []
    mesh_faces = []

    mesh_verts.append([bounds[0][0]*scaler[0], bounds[1][0]*scaler[1],0])
    mesh_verts.append([bounds[0][1]*scaler[0], bounds[1][0]*scaler[1],0])
    mesh_verts.append([bounds[0][1]*scaler[0], bounds[1][1]*scaler[1],0])
    mesh_verts.append([bounds[0][0]*scaler[0], bounds[1][1]*scaler[1],0])
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
                vec1 = [(primitive.start[0])*scaler[0], (primitive.start[1])*scaler[1],0]
            else:
                vec1 = [(primitive.start[0] + offset[0])*scaler[0], (primitive.start[1] + offset[1])*scaler[1],0]
            mesh_verts.append(vec1)
            mesh_i+=1

    me = bpy.data.meshes.new(name)
    me.materials.append(material)
    me.from_pydata(mesh_verts, mesh_edges, mesh_faces)
    me.validate()
    me.update()
    MeshObj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(MeshObj)

    MeshObj.select_set(True)
    bpy.context.view_layer.objects.active = MeshObj
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_mode(type = 'FACE')
    bpy.ops.mesh.edge_face_add()
    bpy.ops.uv.cube_project(cube_size=1, scale_to_bounds=True)
 
    bpy.ops.object.mode_set(mode='OBJECT')
    DeselectAll()

    return MeshObj

def Extrude(ob, extrude_amount, material = None):

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0, 0, extrude_amount)})

    if material is not None:
        ob.data.materials.append(material)
        bpy.ops.mesh.select_all(action='INVERT')
        ob.active_material_index = 1
        bpy.ops.object.material_slot_assign()
    
    bpy.ops.object.mode_set(mode='OBJECT')

def CreateModel(name, source_folder, ctx, pcb_instance=None, extrude=False):

    mat = bpy.data.materials.new(name = name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texImage.image = bpy.data.images.load(os.path.join(source_folder, name + '.png'))
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

    extrudeMat = None
    if extrude:
        extrudeMat = bpy.data.materials.get("ExtrudeMat")
        if extrudeMat is None:
            extrudeMat = bpy.data.materials.new(name = "ExtrudeMat")
        extrudeMat.use_nodes = True
        bsdf = extrudeMat.node_tree.nodes["Principled BSDF"]
        # Base Color
        bsdf.inputs[0].default_value = (0.350555, 0.266215, 0.0896758, 1)
        # Subsurface factor
        bsdf.inputs[1].default_value = 0.05
        extrudeMat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

    mesh = None
    scaler = mathutils.Vector((1, 1, 1))

    if units == "metric":
        scaler = mathutils.Vector((.001, .001, .001))
    if units == "inch":
        scaler = mathutils.Vector((.0254, .0254, .0254))

    if(pcb_instance is not None):
        if(pcb_instance.outline_layer is not None):
            outline = pcb_instance.outline_layer

            mesh = RenderOutline(
                name,
                outline,
                mat,
                None, #-mathutils.Vector((ctx.origin_in_inch[0], ctx.origin_in_inch[1], 0))
                scaler,
                )

    else:
        bounds = ctx.first_bounds
        mesh = RenderBounds(
                name,
                bounds,
                scaler,
                mat,
                )
    
    if mesh is None:
        bounds = pcb_instance.layers[0].bounds
        mesh = RenderBounds(name, bounds, scaler, mat)

    if extrude and mesh:
        Extrude(mesh, 0.0016, extrudeMat)
        
    return mesh

# Rendering

def CreateImage(name, layers, ctx, OUTPUT_FOLDER, w=512, h=512, pcb_instance=None):
     
    layers_to_render = layers
    if(pcb_instance is not None):
        if pcb_instance.outline_layer is not None:
            layers_to_render.insert(0, pcb_instance.outline_layer)
    FileName = name + time.strftime("%Y-%m-%d_%H%M%S")
    ctx.render_layers(layers_to_render, os.path.join(OUTPUT_FOLDER, FileName +'.png'), theme.THEMES['default'], max_width=w, max_height=h)
    return FileName

class PCB_Generate(Operator):
    bl_idname = "pcb.generate"
    bl_label = "Generate"
    bl_description = "Warning: Files in Output folder might be overriden"

    def execute(self, context):

        RegisterProgress()
        UpdateProgress(0)

        global units

        if(context.scene.PickAndPlace == 'SELF' and context.scene.model_folder == "" and (context.scene.placeTop != "" or context.scene.placeBottom != "")):
            ShowMessageBox("Please enter path to Your models library", "Error", 'ERROR')
            return {'CANCELLED'}

        # Placement list
        if(context.scene.placeTop is not ''): ReadPlacement_csv(context.scene.placeTop, context.scene.PickAndPlace, context.scene.model_folder)    
        UpdateProgress(33)
        if(context.scene.placeBottom is not ''): ReadPlacement_csv(context.scene.placeBottom, context.scene.PickAndPlace, context.scene.model_folder)       
        UpdateProgress(66)

        if(str(context.scene.output_path) == ""):
            ShowMessageBox("Please enter path to output folder", "Error", 'ERROR')
            return {'CANCELLED'}
        if(context.scene.expand is not None):
            if(context.scene.expand):
                # Create a new drawing context
                ctx = GerberCairoContext()
                # Preprocess and load layers from strings
                string_up_layers     = [context.scene.edg, context.scene.pu, context.scene.su, context.scene.cu, context.scene.mu, context.scene.drl, context.scene.drl2]
                up_layers = []
                string_bottom_layers = [context.scene.edg, context.scene.pb, context.scene.sb, context.scene.cb, context.scene.mb, context.scene.drl, context.scene.drl2]
                bottom_layers = []
                for stringlayer in string_up_layers:
                    if(stringlayer is not None and stringlayer is not ""):
                        up_layers.append(load_layer(stringlayer))
                for stringlayer in string_bottom_layers:
                    if(stringlayer is not None and stringlayer is not ""):
                        bottom_layers.append(load_layer(stringlayer))

                if len(up_layers) > 0:
                    units = up_layers[0].cam_source.units

                # Render images
                Top_layer_FileName = CreateImage("Top_layer", up_layers, ctx, context.scene.output_path, context.scene.width, context.scene.height)
                UpdateProgress(75)
                Bottom_layer_FileName = CreateImage("Bottom_layer", bottom_layers, ctx, context.scene.output_path, context.scene.width, context.scene.height)
                UpdateProgress(85)
                # Create models
                Top_layer = CreateModel(Top_layer_FileName, context.scene.output_path, ctx, extrude = True)
                Move(Top_layer, distance=-0.0016)
                UpdateProgress(95)
                Bottom_layer = CreateModel(Bottom_layer_FileName, context.scene.output_path, ctx)
                Move(Bottom_layer, distance=-0.00161)


        if(str(context.scene.gerber_folder) == ""):
            ShowMessageBox("Please enter path to folder with gerber files", "Error", 'ERROR')
            return {'CANCELLED'}
        else:
            # Create a new drawing context
            ctx = GerberCairoContext()
            # Create a new PCB instance
            pcb = PCB.from_directory(context.scene.gerber_folder)
            # Render images

            if len(pcb.layers) > 0:
                units = pcb.layers[0].cam_source.units
            
            Top_layer_FileName = CreateImage("Top_layer", pcb.top_layers, ctx, context.scene.output_path, context.scene.width, context.scene.height, pcb_instance = pcb)
            UpdateProgress(75)
            Bottom_layer_FileName = CreateImage("Bottom_layer", pcb.bottom_layers, ctx, context.scene.output_path, context.scene.width, context.scene.height, pcb_instance = pcb)
            UpdateProgress(85)
            # Create models
            Top_layer = CreateModel(Top_layer_FileName, context.scene.output_path, ctx, pcb_instance = pcb, extrude = True)
            Move(Top_layer, distance=-0.0016)
            UpdateProgress(95)
            Bottom_layer = CreateModel(Bottom_layer_FileName, context.scene.output_path, ctx, pcb_instance = pcb)
            Move(Bottom_layer, distance=-0.00161)
            
        ChangeArea('VIEW_3D', 'MATERIAL')
        ChangeClipping(0.001)
        EndProgress()
        #ShowMessageBox("Some files might be overridden in folder: "+context.scene.output_path, "Warning", 'IMPORT')
        #PurgeOrphanData()
        return {'FINISHED'}


        