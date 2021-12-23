import bpy

scene = bpy.context.scene
out = scene.frame_end - scene.frame_start + 1
print("[" + str(out) + "]")
print("|" + str(scene.frame_start) + "|")
print("%" + str(bpy.context.scene.render.file_extension) + "%")
