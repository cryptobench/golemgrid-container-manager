import bpy

scene = bpy.context.scene
out = scene.frame_end - scene.frame_start + 1
print("[" + out + "]")
