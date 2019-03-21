import bpy
#Rotate and Scale Armature
bpy.ops.object.select_all(action='TOGGLE')
bpy.ops.object.select_pattern(pattern="*Armature*")
bpy.ops.transform.resize(value=(8, 8, 8), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
bpy.ops.transform.rotate(value=1.5708, axis=(1, 0, 0), constraint_axis=(True, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
bpy.ops.object.select_all(action='TOGGLE')
#Select Expressions
bpy.ops.object.select_pattern(pattern="*Blink*")
bpy.ops.object.select_pattern(pattern="*Attack*")
bpy.ops.object.select_pattern(pattern="*Ouch*")
bpy.ops.object.select_pattern(pattern="*Talk*")
bpy.ops.object.select_pattern(pattern="*Capture*")
bpy.ops.object.select_pattern(pattern="*Ottotto*")
bpy.ops.object.select_pattern(pattern="*Escape*")
bpy.ops.object.select_pattern(pattern="*Half*")
bpy.ops.object.select_pattern(pattern="*Pattern*")
bpy.ops.object.select_pattern(pattern="*Result*")
bpy.ops.object.select_pattern(pattern="*Harf*")
bpy.ops.object.select_pattern(pattern="*Hot*")
bpy.ops.object.select_pattern(pattern="*Heavy*")
bpy.ops.object.select_pattern(pattern="*Voice*")
bpy.ops.object.select_pattern(pattern="*Fura*")
bpy.ops.object.select_pattern(pattern="*Catch*")
bpy.ops.object.select_pattern(pattern="*Cliff*")
bpy.ops.object.select_pattern(pattern="*FLIP*")
bpy.ops.object.select_pattern(pattern="*Bound*")
bpy.ops.object.select_pattern(pattern="*Down*")
bpy.ops.object.select_pattern(pattern="*Final*")
bpy.ops.object.select_pattern(pattern="*Result*")
#Move to another Layer
bpy.ops.object.move_to_layer(layers=(False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
bpy.context.scene.layers[1] = True
bpy.ops.object.select_all(action='TOGGLE')
bpy.ops.object.select_pattern(pattern="*Openblink*")
bpy.ops.object.select_pattern(pattern="*FaceN*")
bpy.ops.object.move_to_layer(layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
bpy.ops.object.select_all(action='TOGGLE')
bpy.context.scene.layers[1] = False
#Deselect all
for obj in bpy.data.objects:
    obj.select = False
#Move Armature to separate layer
bpy.ops.object.select_pattern(pattern="*Armature*")
bpy.ops.object.move_to_layer(layers=(False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False))
