import bpy, os

# Select Expressions
mesh_expr = ["*Blink*", "*Attack*", "*Ouch*", "*Talk*", "*Capture*", "*Ottotto*", "*Escape*", "*Half*", "*Pattern*", "*Result*", "*Harf*","*Hot*", "*Heavy*", "*Voice*", "*Fura*", "*Throw*", "*Catch*", "*Cliff*", "*FLIP*", "*Bound*", "*Down*", "*Bodybig*", "*Final*", "*Result*", "*StepPose*", "*Sorori*", "*Fall*", "*Appeal*", "*DamageFlyFront*", "*CameraHit*"]

# Make collections for each expressions
bpy.ops.object.select_all(action='DESELECT')
for exp in mesh_expr:
    bpy.ops.object.select_pattern(pattern=exp)
    selectNum = 0
    for obj in bpy.data.objects:
        if obj.select_get():
            selectNum += 1
            print(exp + " -> " + obj.name)

    co = bpy.data.collections
    if selectNum > 0:
        if exp in co:
            collect = co[exp]
        else:
            collect = co.new(name=exp)
            bpy.context.view_layer.active_layer_collection.collection.children.link(collect)
        
        for obj in bpy.data.objects:
            if obj.select_get():
                bpy.ops.collection.objects_remove_active()
                collect.objects.link(obj)

        collect.hide_viewport = True
        collect.hide_render = True

    bpy.ops.object.select_all(action='DESELECT')

#bpy.ops.object.select_all(action='TOGGLE')
#bpy.ops.object.select_pattern(pattern="*Openblink*")
#bpy.ops.object.select_pattern(pattern="*FaceN*")

# Change image filepaths to be relative to the Blender file
for image in bpy.data.images:
    filename = os.path.basename(image.filepath)
    image.filepath = os.path.join("//", filename)
