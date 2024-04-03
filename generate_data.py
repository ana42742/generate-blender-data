import os
import json
import bpy
import mathutils
import numpy as np
import math
import random

def listify_matrix(matrix):
    matrix_list = []
    for row in matrix:
        matrix_list.append(list(row))
    return matrix_list

def get_split(fp, json_file, radius=1, scale=[1,1,1]):
    '''
    Arguments
    =========
    fp: Path to root directory where generated data will be stored
    json_file: Name of generated JSON file
    radius: Radius of sphere along which the camera moves to render views
    scale: Scale of the sphere
    '''
    # Get scene pointer
    scene = bpy.context.scene    
    MAX_FRAME = scene.frame_end
    RESOLUTION = 800
    COLOR_DEPTH = 8
    FORMAT = 'PNG'
    cam = scene.objects['Camera']
    fp = bpy.path.abspath(fp)
    if not os.path.exists(fp):
        os.makedirs(fp)
        os.makedirs(fp+'/images')   
    if not os.path.exists(fp+'/images'):
        os.makedirs(fp+'/images')
    # Data to store in JSON file
    out_data = {
        'camera_angle_x': (bpy.data.objects['Camera'].data.angle_x),
    }
    # Render Optimizations
    bpy.context.scene.render.use_persistent_data = True
    # Set up rendering of depth map.
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    links = tree.links
    bpy.context.scene.render.image_settings.file_format = str(FORMAT)
    bpy.context.scene.render.image_settings.color_depth = str(COLOR_DEPTH)
    # Background
    bpy.context.scene.render.dither_intensity = 0.0
    bpy.context.scene.render.film_transparent = True
    # Set scene constraints
    scene.render.resolution_x = RESOLUTION
    scene.render.resolution_y = RESOLUTION
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.image_settings.color_mode = 'RGBA'
    # Initialise output data for each view
    out_data['frames'] = []
    img_dir = './train/images/'
    # Set the Active Camera
    scene.camera = cam
    # Skip frames while rendering val and test sets
    step = 1
    if "val" in fp:
        step = 3
        img_dir = './val/images/'
    if "test" in fp:
        step = 3
        img_dir = './test/images/'
    # Loop to render views for each frame
    j = 0
    for i in range(0, MAX_FRAME, step):
        # Randomly generate camera rotations within the upper hemisphere
        for _ in range(4):  # Iterate for each camera
            # Randomly generate camera rotations within the upper hemisphere
            # Sample random angles
            theta = random.random() * 2 * math.pi
            phi = random.random() * 2 * math.pi
            # Uniform sample from unit sphere, given theta and phi
            unit_x = math.cos(theta) * math.sin(phi)
            unit_y = math.sin(theta) * math.sin(phi)
            unit_z = abs( math.cos(phi) )
            unit = mathutils.Vector((unit_x, unit_y, unit_z))
            point = radius * mathutils.Vector(scale) * unit
            # Set camera location
            cam.location = point
            # Get origin point of the scene (0, 0, 0)
            origin = mathutils.Vector((0, 0, 0))
            # Calculate direction vector from camera to origin
            direction = cam.location - origin
            direction.normalize()
            # Set camera rotation to align with direction vector
            cam.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
            # Determine the current frame and Set it
            frame = int((i / (MAX_FRAME - 1)) * MAX_FRAME)
            # frame = j
            bpy.context.scene.frame_set(frame)
            print('Time:', frame)
            # Set the frame name (for render and to save reference in transforms.json)
            view_name = 'r_{0:04d}'.format(j)     
            # Set the rendering file_path
            scene.render.filepath = fp + '/images/' + view_name        
            # Render
            bpy.ops.render.render(write_still=True)         
            # Save individual frame data
            frame_data = {
                'file_path': img_dir + view_name,
                'rotation': (cam.rotation_euler.x, cam.rotation_euler.y, cam.rotation_euler.z),
                'time': float(i / (MAX_FRAME - 1)),
                'transform_matrix': listify_matrix(cam.matrix_world),
            }        
            # Append to the output file
            out_data['frames'].append(frame_data)
            j += 1
    with open(fp + '/' + json_file, 'w') as out_file:
        json.dump(out_data, out_file, indent=4)
