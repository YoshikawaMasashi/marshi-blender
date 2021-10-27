# from https://github.com/EternalTrail/eeVR
import os
import math

import bpy


class Eevee360(bpy.types.Operator):

    bl_idname = "marshi.eevee360"
    bl_label = "Eevee 360"
    bl_options = {"REGISTER",}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"
    
    def execute(self, context):
        resolution = 3840

        camera_origin = bpy.context.scene.camera
        original_resolution = [
            bpy.context.scene.render.resolution_x,
            bpy.context.scene.render.resolution_y
        ]

        bpy.ops.object.camera_add()
        camera = bpy.context.object
        camera.name = 'eeVR_camera'
        bpy.context.scene.camera = camera

        camera.matrix_world = camera_origin.matrix_world
        camera.data.stereo.interocular_distance = camera_origin.data.stereo.interocular_distance
        camera.data.clip_start = camera_origin.data.clip_start
        camera.data.clip_end = camera_origin.data.clip_end

        camera.data.type = 'PANO'
        camera.data.stereo.convergence_mode = 'PARALLEL'
        camera.data.stereo.pivot = 'CENTER'
        camera.data.angle = math.pi / 2

        bpy.context.scene.render.resolution_x = resolution
        bpy.context.scene.render.resolution_y = resolution

        eul = camera.rotation_euler.copy()
        direction_offsets = {}
        direction_offsets['front'] = list(eul)
        #back
        eul.rotate_axis('Y', math.pi)
        direction_offsets['back'] = list(eul)
        #top
        eul = camera.rotation_euler.copy()
        eul.rotate_axis('X', math.pi/2)
        direction_offsets['top'] = list(eul)
        #bottom
        eul.rotate_axis('X', math.pi)
        direction_offsets['bottom'] = list(eul)
        #left
        eul = camera.rotation_euler.copy()
        eul.rotate_axis('Y', math.pi/2)
        direction_offsets['left'] = list(eul)
        #right
        eul.rotate_axis('Y', math.pi)
        direction_offsets['right'] = list(eul)

        os.makedirs(bpy.path.abspath("//eevee360"), exist_ok=True)

        directions = ['front', 'back', 'top', 'bottom', 'left', 'right']
        imgs = []
        for direction in directions:
            camera.rotation_euler = direction_offsets[direction]
            filepath = bpy.path.abspath(f"//eevee360\\{direction}.png")
            bpy.ops.render.render()
            img = bpy.data.images['Render Result']
            img.save_render(filepath)

        bpy.data.objects.remove(camera)
        bpy.context.scene.render.resolution_x = original_resolution[0]
        bpy.context.scene.render.resolution_y = original_resolution[1]

        return {'FINISHED'}
