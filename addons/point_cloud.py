# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
    'name': 'Point Cloud',
    'author': 'Vincent Gires',
    'version': (0, 0, 1),
    'blender': (2, 7, 9),
    'location': 'Tool shelves (3D View, Image Editor)',
    'warning': '',
    'wiki_url': '',
    'tracker_url': '',
    'category': '3D View'}


import bpy
import bgl

cloud_coordinates = []

## CUSTOM PROPERTIES ##
#######################

class PointCloudProperties(bpy.types.PropertyGroup):
    color_pass = bpy.props.StringProperty(
        name='Color pass')
    
    position_pass = bpy.props.StringProperty(
        name='Position pass')
    
    point_detail = bpy.props.FloatProperty(
        name='Detail',
        default=0.25,
        soft_min=0.01,
        soft_max=1.0)
    
    point_size = bpy.props.IntProperty(
        name='Size',
        default=1,
        soft_min=1)


## FUNCTIONS ##
###############

def draw_pointcloud_gl():
    context = bpy.context
    scene = context.scene
    
    if not cloud_coordinates:
        return None
    
    detail = scene.point_cloud.point_detail
    length_full = len(cloud_coordinates)
    length_detail = length_full*detail
    step = length_full/length_detail
    step = int(step)
    size = scene.point_cloud.point_size
    
    bgl.glPointSize(size)
    bgl.glBegin(bgl.GL_POINTS)
    for coord in cloud_coordinates[::step]:
        color, position = coord
        bgl.glColor3f(color[0], color[1], color[2])
        bgl.glVertex3f(position[0], position[1], position[2])
    bgl.glEnd()


def get_positions(context):
    scene = context.scene
    data = bpy.data
    
    position_src = scene.point_cloud.position_pass
    position_data = data.images[position_src]
    position_pixels = list(position_data.pixels)
    
    coordinates = []
    cpt_rgba = 0
    pixel_rgb = []

    for value in position_pixels:
        
        if cpt_rgba <= 2:
            pixel_rgb.append(value)
            
        cpt_rgba += 1
        
        if cpt_rgba == 3:
            coordinates.append(pixel_rgb)
            pixel_rgb = []
        
        elif cpt_rgba == 4:
            cpt_rgba = 0
    
    return coordinates


def get_coordinates(context):
    scene = context.scene
    data = bpy.data
    
    position_src = scene.point_cloud.position_pass
    color_src = scene.point_cloud.color_pass
    position_data = data.images[position_src]
    color_data = data.images[color_src]
    position_pixels = list(position_data.pixels)
    color_pixels = list(color_data.pixels)
    
    cpt_rgba = 0
    pixel_rgb_position = []
    pixel_rgb_color = []

    for value_position, value_color in zip(position_pixels, color_pixels):
        
        if cpt_rgba <= 2:
            pixel_rgb_position.append(value_position)
            pixel_rgb_color.append(value_color)
            
        cpt_rgba += 1
        
        if cpt_rgba == 3:
            cloud_coordinates.append((pixel_rgb_position, pixel_rgb_color))
            pixel_rgb_position = []
            pixel_rgb_color = []
            
        elif cpt_rgba == 4:
            cpt_rgba = 0


def create_mesh(name, origin, verts, edges, faces):
    me = bpy.data.meshes.new(name+'Mesh')
    ob = bpy.data.objects.new(name, me)
    ob.location = origin
    ob.show_name = True
    bpy.context.scene.objects.link(ob)
    me.from_pydata(verts, edges, faces)
    me.update(calc_edges=True)
    
    return ob


## PANEL ##
###########

class PointCloud3DViewPanel(bpy.types.Panel):
    bl_label = 'Point Cloud'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Custom'
 
    def draw(self, context):
        scene = context.scene
        data = bpy.data
        layout = self.layout
        
        col = layout.column(align=True)
        col.prop_search(scene.point_cloud, 'position_pass',
                        data, 'images', icon='FILE_IMAGE')
        col.prop_search(scene.point_cloud, 'color_pass',
                        data, 'images', icon='FILE_IMAGE')
        
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator('scene.pointcloud_generate')
        row.operator('scene.pointcloud_clear')
        col.prop(scene.point_cloud, 'point_detail', slider=True)
        col.prop(scene.point_cloud, 'point_size')
        col.operator('scene.pointcloud_generate_mesh')


## OPERATOR ##
##############

class PointCloudGenerateOpenGl(bpy.types.Operator):
    bl_idname = 'scene.pointcloud_generate'
    bl_label = 'Generate cloud'
    bl_description = 'Generate cloud of point based on the position pass'
    
    @classmethod
    def poll(cls, context):
        position = context.scene.point_cloud.position_pass
        color = context.scene.point_cloud.color_pass
        return position and color
    
    def execute(self, context):
        scene = context.scene
        coordinates = get_coordinates(context)
        return{'FINISHED'}


class PointCloudClearOpenGl(bpy.types.Operator):
    bl_idname = 'scene.pointcloud_clear'
    bl_label = 'Clear'
    bl_description = 'Remove cloud from the viewport'
    
    @classmethod
    def poll(cls, context):
        return cloud_coordinates
    
    def execute(self, context):
        cloud_coordinates.clear()
        return{'FINISHED'}


class PointCloudGenerateMesh(bpy.types.Operator):
    bl_idname = 'scene.pointcloud_generate_mesh'
    bl_label = 'Create mesh'
    bl_description = 'Generate cloud of vertices based on the position pass'
    
    @classmethod
    def poll(cls, context):
        position = context.scene.point_cloud.position_pass
        return position
    
    def execute(self, context):
        scene = context.scene
        
        coordinates = get_positions(context)
        origin = (0,0,0)
        position_objects = create_mesh(
            'Position_Cloud', origin, coordinates, [], [])
        
        return{'FINISHED'}

opengl_handle = [None]

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.point_cloud = \
        bpy.props.PointerProperty(type=PointCloudProperties)
    opengl_handle[0] = bpy.types.SpaceView3D.draw_handler_add(
        draw_pointcloud_gl, (), 'WINDOW', 'POST_VIEW')
    
def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.point_cloud
    bpy.types.SpaceView3D.draw_handler_remove(
        opengl_handle[0], 'WINDOW')

    
if __name__ == '__main__':
    register()


