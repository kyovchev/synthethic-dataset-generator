import bpy
import struct
import math
import os

# Params
STL_PATH = './model.stl'
OUTPUT_DIR = './output'
ROLL = 30
PITCH = 60
YAW = 45

os.makedirs(OUTPUT_DIR, exist_ok=True)


# Load STL file
def load_binary_stl(filepath):
    with open(filepath, 'rb') as f:
        f.read(80)  # header
        num_triangles = struct.unpack('<I', f.read(4))[0]
        vertices = []
        faces = []
        for i in range(num_triangles):
            f.read(12)
            v1 = struct.unpack('<fff', f.read(12))
            v2 = struct.unpack('<fff', f.read(12))
            v3 = struct.unpack('<fff', f.read(12))
            vertices.extend([v1, v2, v3])
            faces.append((3*i, 3*i+1, 3*i+2))
            f.read(2)

    mesh = bpy.data.meshes.new('ImportedSTL')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new('STLObject', mesh)
    bpy.context.collection.objects.link(obj)
    return obj


# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Background
bpy.context.scene.world.use_nodes = True
bg = bpy.context.scene.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0, 0, 0, 1)

# Camera
cam_data = bpy.data.cameras.new('Camera')
cam = bpy.data.objects.new('Camera', cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (0, 0, 1.5)
cam.rotation_euler = (0, 0, 0)

# Camera params
cam_data = cam.data
focal_length = cam_data.lens
sensor_width = cam_data.sensor_width
print(f'Focal length (mm): {focal_length}')
print(f'Sensor width (mm): {sensor_width}')

# Scene params (in pixels)
scene = bpy.context.scene
res_x = scene.render.resolution_x
res_y = scene.render.resolution_y
print(f'Resolution: {res_x}x{res_y}')

# Calculate camera intrinsics
# Calculate fx and fy (pixels)
fx = (focal_length * res_x) / sensor_width
sensor_height = sensor_width * (res_y / res_x)
fy = (focal_length * res_y) / sensor_height
print(f'fx: {fx:.2f} px')
print(f'fy: {fy:.2f} px')
# Calculate optical center
cx = res_x / 2
cy = res_y / 2
print(f'Optical center: ({cx}, {cy})')

# Light
light_data = bpy.data.lights.new(name='Light', type='SUN')
light_data.energy = 5.0
light = bpy.data.objects.new(name='Light', object_data=light_data)
bpy.context.collection.objects.link(light)
light.location = (0, 0, 2)

# Load the object
mat = bpy.data.materials.new(name='CustomColor')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.0, 0.5, 1.0, 1.0)
bsdf.inputs['Roughness'].default_value = 0.4

obj = load_binary_stl(STL_PATH)

if obj.data.materials:
    obj.data.materials[0] = mat
else:
    obj.data.materials.append(mat)

bpy.context.view_layer.objects.active = obj

obj.rotation_euler = (
    math.radians(ROLL),
    math.radians(PITCH),
    math.radians(YAW)
)

filename = f'pose_{ROLL:03d}_{PITCH:03d}_{YAW:03d}.png'
img_path = os.path.join(OUTPUT_DIR, filename)
bpy.context.scene.render.filepath = img_path
bpy.ops.render.render(write_still=True)

print(f'Generated image {img_path}')
