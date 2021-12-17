import bpy

scene = bpy.context.scene
out = scene.frame_end - scene.frame_start + 1
print("[" + str(out) + "]")
print("|" + str(scene.frame_start) + "|")
