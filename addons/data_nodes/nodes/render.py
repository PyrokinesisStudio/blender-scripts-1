import bpy
from bpy.types import NodeTree, Node, NodeSocket
from data_nodes.utils import send_value


class RenderNode(Node):
    '''Render node'''
    bl_idname = 'RenderNodeType'
    bl_label = 'Render'
    
    on_render = bpy.props.FloatProperty(
        name='On render', default=0)
    
    def init(self, context):
        self.outputs.new('NodeSocketFloat', "on_render")
     
    def update(self):
        send_value(self.outputs, self.on_render)
     
    def draw_label(self):
        return "Render"

