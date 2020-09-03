import bpy, os

# Select Expressions
mesh_expr = ["*Blink*", "*Attack*", "*Ouch*", "*Talk*", "*Capture*", "*Ottotto*", "*Escape*", "*Half*", "*Pattern*", "*Result*", "*Harf*","*Hot*", "*Heavy*", "*Voice*", "*Fura*", "*Throw*", "*Catch*", "*Cliff*", "*FLIP*", "*Bound*", "*Down*", "*Bodybig*", "*Final*", "*Result*", "*StepPose*", "*Sorori*", "*Fall*", "*Appeal*", "*DamageFlyFront*", "*CameraHit*"]

# Move expression objects to the second layer
bpy.ops.object.select_all(action='DESELECT')
for exp in mesh_expr:
    bpy.ops.object.select_pattern(pattern=exp)
    # Move to another Layer
    bpy.ops.object.move_to_layer(layers=(False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
    bpy.ops.object.select_all(action='DESELECT')

# Keep default expressions on the first layer
bpy.ops.object.select_pattern(pattern="*Openblink*")
bpy.ops.object.select_pattern(pattern="*FaceN*")
bpy.ops.object.move_to_layer(layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
bpy.ops.object.select_all(action='DESELECT')

# Move Armature to separate (11th) layer
bpy.ops.object.select_pattern(pattern="*Armature*")
bpy.ops.object.move_to_layer(layers=(False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False))

# Change image filepaths to be relative to the Blender file
for image in bpy.data.images:
    filename = os.path.basename(image.filepath)
    image.filepath = os.path.join("//", filename)
