import bpy
import bmesh
import collections
from typing import Optional, Any, List
import math

from . import eevee360


bl_info = {
    "name": "marshi",
    "author": "marshi",
    "description": "marshi blender addon",
    "version": (0, 0, 1),
    "blender": (2, 90, 0),
    "location": "",
    "url": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "marshi"
}

class SquareSkin(bpy.types.Operator):

    bl_idname = "marshi.square_skin"
    bl_label = "Square Skin"
    bl_options = {"REGISTER", "UNDO"}

    amount = bpy.props.FloatProperty(
        name="amount",
        default=0.1,
    )

    def is_path(self, bm):
        counter = collections.Counter(sum([list(e.verts) for e in bm.edges if e.select], []))
        if len([v for v in counter.values() if v != 1 and v != 2]) > 0:
            return False
        if len([v for v in counter.values() if v == 1]) != 2:
            return False
        if len([e for e in bm.edges if e.select]) != len([v for v in bm.verts if v.select]) - 1:
            return False
        return True
    
    def path_list(self, bm) -> List[Any]:
        selected_edges = [e for e in bm.edges if e.select]
        v_to_e = {}
        for e in selected_edges:
            for v in e.verts:
                if v in v_to_e:
                    v_to_e[v].append(e)
                else:
                    v_to_e[v] = [e]

        def other_v(v, e):
            return list(set(e.verts) - set([v]))[0]

        def next_e(v, e) -> Optional[Any]:
            edges = v_to_e[v]
            if len(edges) == 2:
                next_edge = list(set(edges) - set([e]))[0]
                return next_edge
            else:
                return None

        first_v = None
        for v in v_to_e:
            if len(v_to_e[v]) == 1:
                first_v = v
                break

        path = [first_v]
        current_v = first_v
        current_e = v_to_e[current_v][0]
        while True:
            next_v = other_v(current_v, current_e)
            path.append(next_v)
            if next_e(next_v, current_e) is None:
                break
            else:
                current_v, current_e = next_v, next_e(next_v, current_e)
        return path

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode == "EDIT_MESH"

    def execute(self, context):
        bm = bmesh.from_edit_mesh(context.edit_object.data)

        if not self.is_path(bm):
            self.report({'WARNING'}, "selected if not path")
            return {'CANCELLED'}

        path = self.path_list(bm)
        new_verts_list = []
        for i, v in enumerate(path):
            if i == 0:
                verts = [v, path[1], path[2]]
                axis1 = (verts[2].co - verts[1].co).cross(verts[1].co - verts[0].co)
                axis1 = axis1.normalized()
                axis2 = (verts[1].co - verts[0].co).cross(axis1)
                axis2 = axis2.normalized()

                v1 = bm.verts.new(v.co + 0.5 * self.amount * (axis1 + axis2))
                v2 = bm.verts.new(v.co + 0.5 * self.amount * (axis1 - axis2))
                v3 = bm.verts.new(v.co + 0.5 * self.amount * (-axis1 - axis2))
                v4 = bm.verts.new(v.co + 0.5 * self.amount * (-axis1 + axis2))
                bm.faces.new((v1, v2, v3, v4))
                new_verts = [v1, v2, v3, v4]
                new_verts_list.append(new_verts)
            elif i == len(path) - 1:
                verts = [v, path[i-1], path[i-2]]
                axis1 = (verts[2].co - verts[1].co).cross(verts[1].co - verts[0].co)
                axis1 = axis1.normalized()
                axis2 = (verts[1].co - verts[0].co).cross(axis1)
                axis2 = axis2.normalized()

                v1 = bm.verts.new(v.co + 0.5 * self.amount * (axis1 + axis2))
                v2 = bm.verts.new(v.co + 0.5 * self.amount * (axis1 - axis2))
                v3 = bm.verts.new(v.co + 0.5 * self.amount * (-axis1 - axis2))
                v4 = bm.verts.new(v.co + 0.5 * self.amount * (-axis1 + axis2))
                bm.faces.new((v1, v2, v3, v4))
                new_verts = [v1, v2, v3, v4]
                new_verts_list.append(new_verts)
            else:
                verts = [path[i-1], v, path[i+1]]
                axis1 = (verts[2].co - verts[1].co).cross(verts[1].co - verts[0].co)
                axis1 = axis1.normalized()
                axis2 = ((verts[0].co - verts[1].co).normalized() + (verts[2].co - verts[1].co).normalized())
                axis2 = axis2.normalized()
                axis2 = axis2 / math.sin((verts[0].co - verts[1].co).angle(axis2))

                v1 = bm.verts.new(v.co + 0.5 * self.amount * (axis1 + axis2))
                v2 = bm.verts.new(v.co + 0.5 * self.amount * (axis1 - axis2))
                v3 = bm.verts.new(v.co + 0.5 * self.amount * (-axis1 - axis2))
                v4 = bm.verts.new(v.co + 0.5 * self.amount * (-axis1 + axis2))
                new_verts = [v1, v2, v3, v4]
                new_verts_list.append(new_verts)
        
        for i in range(len(path) - 1):
            new_verts1 = new_verts_list[i]
            new_verts2 = new_verts_list[i + 1]
            vert1, vert2 = path[i], path[i + 1]

            corres_vert = []
            for v1 in new_verts1:
                angles = [(vert2.co - vert1.co).angle(v2.co - v1.co) for v2 in new_verts2]
                argmin = min(enumerate(angles), key = lambda x:x[1])[0]
                corres_vert.append(new_verts2[argmin])
                
            try:
                bm.faces.new((new_verts1[0], new_verts1[1], corres_vert[1], corres_vert[0]))
                bm.faces.new((new_verts1[1], new_verts1[2], corres_vert[2], corres_vert[1]))
                bm.faces.new((new_verts1[2], new_verts1[3], corres_vert[3], corres_vert[2]))
                bm.faces.new((new_verts1[3], new_verts1[0], corres_vert[0], corres_vert[3]))
            except:
                pass

        for v in path:
            bm.verts.remove(v)

        bm.normal_update()
        bmesh.update_edit_mesh(context.edit_object.data)
        return {'FINISHED'}


class CircleSkin(bpy.types.Operator):

    bl_idname = "marshi.circle_skin"
    bl_label = "Circle Skin"
    bl_options = {"REGISTER", "UNDO"}

    
    amount : bpy.props.FloatProperty(
        name="amount",
        default=0.1,
    )
    vertex: bpy.props.IntProperty(
        name="vertex",
        default=16,
        step=4,
        subtype='UNSIGNED',
    ) 


    def is_path(self, bm):
        counter = collections.Counter(sum([list(e.verts) for e in bm.edges if e.select], []))
        if len([v for v in counter.values() if v != 1 and v != 2]) > 0:
            return False
        if len([v for v in counter.values() if v == 1]) != 2:
            return False
        if len([e for e in bm.edges if e.select]) != len([v for v in bm.verts if v.select]) - 1:
            return False
        return True
    
    def path_list(self, bm) -> List[Any]:
        selected_edges = [e for e in bm.edges if e.select]
        v_to_e = {}
        for e in selected_edges:
            for v in e.verts:
                if v in v_to_e:
                    v_to_e[v].append(e)
                else:
                    v_to_e[v] = [e]

        def other_v(v, e):
            return list(set(e.verts) - set([v]))[0]

        def next_e(v, e) -> Optional[Any]:
            edges = v_to_e[v]
            if len(edges) == 2:
                next_edge = list(set(edges) - set([e]))[0]
                return next_edge
            else:
                return None

        first_v = None
        for v in v_to_e:
            if len(v_to_e[v]) == 1:
                first_v = v
                break

        path = [first_v]
        current_v = first_v
        current_e = v_to_e[current_v][0]
        while True:
            next_v = other_v(current_v, current_e)
            path.append(next_v)
            if next_e(next_v, current_e) is None:
                break
            else:
                current_v, current_e = next_v, next_e(next_v, current_e)
        return path

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode == "EDIT_MESH"

    def execute(self, context):
        bm = bmesh.from_edit_mesh(context.edit_object.data)

        if not self.is_path(bm):
            self.report({'WARNING'}, "selected if not path")
            return {'CANCELLED'}

        path = self.path_list(bm)
        new_verts_list = []
        for i, v in enumerate(path):
            if i == 0:
                verts = [v, path[1], path[2]]
                axis1 = (verts[2].co - verts[1].co).cross(verts[1].co - verts[0].co)
                axis1 = axis1.normalized()
                axis2 = (verts[1].co - verts[0].co).cross(axis1)
                axis2 = axis2.normalized()

                new_verts = []
                for i in range(self.vertex):
                    theta = 2 * math.pi * i / self.vertex
                    new_vert = bm.verts.new(v.co + 0.5 * self.amount * (math.cos(theta) * axis1 + math.sin(theta) * axis2))
                    new_verts.append(new_vert)
                bm.faces.new(new_verts)
                new_verts_list.append(new_verts)
            elif i == len(path) - 1:
                verts = [v, path[i-1], path[i-2]]
                axis1 = (verts[2].co - verts[1].co).cross(verts[1].co - verts[0].co)
                axis1 = axis1.normalized()
                axis2 = (verts[1].co - verts[0].co).cross(axis1)
                axis2 = axis2.normalized()

                new_verts = []
                for i in range(self.vertex):
                    theta = 2 * math.pi * i / self.vertex
                    new_vert = bm.verts.new(v.co + 0.5 * self.amount * (math.cos(theta) * axis1 + math.sin(theta) * axis2))
                    new_verts.append(new_vert)
                bm.faces.new(new_verts)
                new_verts_list.append(new_verts)
            else:
                verts = [path[i-1], v, path[i+1]]
                axis1 = (verts[2].co - verts[1].co).cross(verts[1].co - verts[0].co)
                axis1 = axis1.normalized()
                axis2 = ((verts[0].co - verts[1].co).normalized() + (verts[2].co - verts[1].co).normalized())
                axis2 = axis2.normalized()
                axis2 = axis2 / math.sin((verts[0].co - verts[1].co).angle(axis2))

                new_verts = []
                for i in range(self.vertex):
                    theta = 2 * math.pi * i / self.vertex
                    new_vert = bm.verts.new(v.co + 0.5 * self.amount * (math.cos(theta) * axis1 + math.sin(theta) * axis2))
                    new_verts.append(new_vert)
                new_verts_list.append(new_verts)
        
        for i in range(len(path) - 1):
            new_verts1 = new_verts_list[i]
            new_verts2 = new_verts_list[i + 1]
            vert1, vert2 = path[i], path[i + 1]

            corres_vert = []
            for v1 in new_verts1:
                angles = [(vert2.co - vert1.co).angle(v2.co - v1.co) for v2 in new_verts2]
                argmin = min(enumerate(angles), key = lambda x:x[1])[0]
                corres_vert.append(new_verts2[argmin])
            
            for i in range(self.vertex):
                j = (i + 1) % self.vertex
                try:
                    bm.faces.new((new_verts1[i], new_verts1[j], corres_vert[j], corres_vert[i]))
                except:
                    pass

        for v in path:
            bm.verts.remove(v)

        bm.normal_update()
        bmesh.update_edit_mesh(context.edit_object.data)
        return {'FINISHED'}


class MarshiMenu(bpy.types.Menu):
    bl_idname = "MarshiMenu"
    bl_label = "Marshi Menu"
    bl_description = "Marshi Menu"

    @classmethod
    def poll(cls, context):
        return (
            (context.object is not None and context.mode == "EDIT_MESH")
            or context.mode == "OBJECT"
        )

    def draw(self, context):
        layout = self.layout

        if context.mode == "EDIT_MESH":
            layout.operator(SquareSkin.bl_idname)
            layout.operator(CircleSkin.bl_idname)

classes = [
    SquareSkin,
    CircleSkin,
    MarshiMenu,

    # eevee360
    eevee360.Eevee360Render,
    eevee360.Eevee360AnimationRender,
    eevee360.Eevee360Panel,
]

addon_keymaps = []

def register_shortcut():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', ctrl=True, shift=True, alt=False)
        kmi.properties.name =  MarshiMenu.bl_idname
        addon_keymaps.append((km, kmi))

def unregister_shortcut():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

def register():
    for c in classes:
        bpy.utils.register_class(c)
    register_shortcut()

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    unregister_shortcut()

if __name__ == "__main__":
    register()
