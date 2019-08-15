#!BPY

"""
Name: 'Super Smash Bros. Ultimate Model Importer (.numdlb)...'
Blender: 277
Group: 'Import'
Tooltip: 'Import *.NUMDLB (.numdlb)'
"""

__author__ = ["Richard Qian (Worldblender)", "Random Talking Bush", "Ploaj"]
__url__ = ["https://gitlab.com/Worldblender/io_scene_numdlb"]
__version__ = "1.3.3"
__bpydoc__ = """\
"""

bl_info = {
    "name": "Super Smash Bros. Ultimate Model Importer",
    "description": "Imports data referenced by NUMDLB files (binary model format used by some games developed by Bandai-Namco)",
    "author": "Richard Qian (Worldblender), Random Talking Bush, Ploaj",
    "version": (1, 3, 3),
    "blender": (2, 80, 0),
    "api": 31236,
    "location": "File > Import",
    "warning": '', # used for warning icon and text in addons panel
    "wiki_url": "https://gitlab.com/Worldblender/io_scene_numdlb",
    "tracker_url": "https://gitlab.com/Worldblender/io_scene_numdlb/issues",
    "category": "Import-Export"}

import bmesh, bpy, math, mathutils, os, struct, sys, time
from bpy_extras import image_utils, node_shader_utils

def reinterpretCastIntToFloat(int_val):
    return struct.unpack('f', struct.pack('I', int_val))[0]

def decompressHalfFloat(bytes):
    if sys.version_info[0] == 3 and sys.version_info[1] > 5:
        return struct.unpack("<e", bytes)[0]
    else:
        float16 = int(struct.unpack('<H', bytes)[0])
        # sign
        s = (float16 >> 15) & 0x00000001
        # exponent
        e = (float16 >> 10) & 0x0000001f
        # fraction
        f = float16 & 0x000003ff

        if e == 0:
            if f == 0:
                return reinterpretCastIntToFloat(int(s << 31))
            else:
                while not (f & 0x00000400):
                    f = f << 1
                    e -= 1
                e += 1
                f &= ~0x00000400
                #print(s,e,f)
        elif e == 31:
            if f == 0:
                return reinterpretCastIntToFloat(int((s << 31) | 0x7f800000))
            else:
                return reinterpretCastIntToFloat(int((s << 31) | 0x7f800000 |
                    (f << 13)))

        e = e + (127 -15)
        f = f << 13
        return reinterpretCastIntToFloat(int((s << 31) | (e << 23) | f))

class MaterialData:
    def __init__(self):
        self.materialName = ""
        self.color1Name = ""
        self.color2Name = ""
        self.bakeName = ""
        self.normalName = ""
        self.emissive1Name = ""
        self.emissive2Name = ""
        self.prmName = ""
        self.envName = ""

    def __repr__(self):
        return "Material name: " + str(self.materialName) + "\t| Color 1 name: " + str(self.color1Name) + "\t| Color 2 name: " + str(self.color2Name) + "\t| Bake name: " + str(self.bakeName) + "\t| Normal name: " + str(self.normalName) + "\t| Emissive 1 name: " + str(self.emissive1Name) + "\t| Emissive 2 name: " + str(self.emissive2Name) + "\t| PRM name: " + str(self.prmName) + "\t| Env name: " + str(self.envName) + "\n"

class WeightData:
    def __init__(self):
        self.boneIDs = []
        self.weights = []

    def __init__(self, boneIDs, weights):
        self.boneIDs = boneIDs
        self.weights = weights

    def __repr__(self):
        return "Bone IDs: " + str(self.boneIDs) + "\t| Weights: " + str(self.weights) + "\n"

class PolygonGroupData:
    def __init__(self):
        self.visGroupName = ""
        self.singleBindName = ""
        self.facepointCount = 0
        self.facepointStart = 0
        self.faceLongBit = 0
        self.verticeCount = 0
        self.verticeStart = 0
        self.verticeStride = 0
        self.UVStart = 0
        self.UVStride = 0
        self.bufferParamStart = 0
        self.bufferParamCount = 0

    def __repr__(self):
        return "Vis group name: " + str(self.visGroupName) + "\t| Single bind name: " + str(self.singleBindName) + "\t| Facepoint count: " + str(self.facepointCount) + "\t| Facepoint start: " + str(self.facepointStart) + "\t| Face long bit: " + str(self.faceLongBit) + "\t| Vertice count: " + str(self.verticeCount) + "\t| Vertice start " + str(self.verticeStart) + "\t| Vertice stride: " + str(self.verticeStride) + "\t| UV start: " + str(self.UVStart) + "\t| UV stride: " + str(self.UVStride) + "\t| Buffer parameter start: " + str(self.bufferParamStart) + "\t| Buffer parameter count: " + str(self.bufferParamCount) + "\n"

class WeightGroupData:
    def __init__(self):
        self.groupName = ""
        self.subGroupNum = 0
        self.weightInfMax = 0
        self.weightFlag2 = 0
        self.weightFlag3 = 0
        self.weightFlag4 = 0
        self.rigInfOffset = 0
        self.rigInfCount =  0

    def __repr__(self):
        return str(self.groupName) + "\t| Subgroup #: " + str(self.subGroupNum) + "\t| Weight info max: " + str(self.weightInfMax) + "\t| Weight flags: " + str(self.weightFlag2) + ", " + str(self.weightFlag3) + ", " + str(self.weightFlag4) + "\t| Rig info offset: " + str(self.rigInfOffset) + "\t| Rig info count: " + str(self.rigInfCount) + "\n"

def findUVImage(matNameQuery, UVMapID=0):
    for mat in Materials_array:
        if (mat.materialName == matNameQuery):
            if (UVMapID > 0):
                return mat.color2Name
            else:
                return mat.color1Name
    return ""

def readVarLenString(file):
    nameBuffer = []
    while('\x00' not in nameBuffer):
        nameBuffer.append(str(file.read(1).decode("utf-8", "ignore")))
    del nameBuffer[-1]
    return ''.join(nameBuffer)

def getModelInfo(context, filepath, image_transparency, texture_ext, use_vertex_colors, use_uv_maps, allow_black, create_rest_action, auto_rotate):
    # Semi-global variables used by this function's hierarchy; cleared every time this function runs
    global dirPath; dirPath = ""
    global MODLName; MODLName = ""
    global SKTName; SKTName = ""
    global MATName; MATName = ""
    global MSHName; MSHName = ""
    global skelName; skelName = ""
    global MODLGrp_array; MODLGrp_array = {}
    global Materials_array; Materials_array = []

    if os.path.isfile(filepath):
        with open(filepath, 'rb') as md:
            dirPath = os.path.dirname(filepath)
            md.seek(0x10, 0)
            # Reads the model file to find information about the other files
            MODLCheck = struct.unpack('<L', md.read(4))[0]
            if (MODLCheck == 0x4D4F444C):
                MODLVerA = struct.unpack('<H', md.read(2))[0]
                MODLVerB = struct.unpack('<H', md.read(2))[0]
                MODLNameOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                SKTNameOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                MATNameOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                md.seek(0x10, 1)
                MSHNameOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                MSHDatOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                MSHDatCount = struct.unpack('<L', md.read(4))[0]
                md.seek(MODLNameOff, 0)
                MODLName = readVarLenString(md)
                md.seek(SKTNameOff, 0)
                SKTName = os.path.join(dirPath, readVarLenString(md))
                md.seek(MATNameOff, 0)
                MATNameStrLen = struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                MATName = os.path.join(dirPath, readVarLenString(md))
                md.seek(MSHNameOff, 0)
                MSHName = os.path.join(dirPath, readVarLenString(md)); md.seek(0x04, 1)
                md.seek(MSHDatOff, 0)
                nameCounter = 0
                for g in range(MSHDatCount):
                    MSHGrpNameOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                    MSHUnkNameOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                    MSHMatNameOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                    MSHRet = md.tell()
                    md.seek(MSHGrpNameOff, 0)
                    meshGroupName = readVarLenString(md)
                    md.seek(MSHMatNameOff, 0)
                    meshMaterialName = readVarLenString(md)
                    if meshGroupName in MODLGrp_array:
                        nameCounter += 1
                        MODLGrp_array[meshGroupName + str(nameCounter * .001)[1:]] = meshMaterialName
                    else:
                        MODLGrp_array[meshGroupName] = meshMaterialName
                        nameCounter = 0
                    md.seek(MSHRet, 0)
                print(MODLGrp_array)
            else:
                raise RuntimeError("%s is not a valid NUMDLB file." % filepath)

        if os.path.isfile(MATName):
            importMaterials(MATName, image_transparency, texture_ext)
        if os.path.isfile(SKTName):
            importSkeleton(context, SKTName, create_rest_action)
        if os.path.isfile(MSHName):
            importMeshes(context, MSHName, texture_ext, use_vertex_colors, use_uv_maps, allow_black)

        # Rotate armature if option is enabled
        if auto_rotate:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.select_pattern(pattern=armaName)
            bpy.ops.transform.rotate(value=math.radians(-90), orient_axis='X', constraint_axis=(True, False, False), orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1)
            bpy.ops.object.select_all(action='TOGGLE')

# Imports the materials
def importMaterials(MATName, image_transparency, texture_ext):
    with open(MATName, 'rb') as mt:
        mt.seek(0x10, 0)
        MATCheck = struct.unpack('<L', mt.read(4))[0]
        if (MATCheck == 0x4D41544C):
            MATVerA = struct.unpack('<H', mt.read(2))[0]
            MATVerB = struct.unpack('<H', mt.read(2))[0]
            MATHeadOff = mt.tell() + struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
            MATCount = struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
            mt.seek(MATHeadOff, 0)
            for m in range(MATCount):
                pe = MaterialData()
                MATNameOff = mt.tell() + struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
                MATParamGrpOff = mt.tell() + struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
                MATParamGrpCount = struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
                MATShdrNameOff = mt.tell() + struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
                MATRet = mt.tell()
                mt.seek(MATNameOff, 0)
                pe.materialName = readVarLenString(mt)
                print("Textures for " + pe.materialName + ":")
                mt.seek(MATParamGrpOff, 0)
                for p in range(MATParamGrpCount):
                    MatParamID = struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
                    MatParamOff = mt.tell() + struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
                    MatParamType = struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
                    MatParamRet = mt.tell()
                    if (MatParamType == 0x0B):
                        mt.seek(MatParamOff + 0x08, 0)
                        TexName = str.lower(readVarLenString(mt))
                        print("(" + hex(MatParamID) + ") for " + TexName)
                        if (MatParamID == 0x5C):
                            pe.color1Name = TexName
                        elif (MatParamID == 0x5D):
                            pe.color2Name = TexName
                        elif (MatParamID == 0x5F):
                            pe.bakeName = TexName
                        elif (MatParamID == 0x60):
                            pe.normalName = TexName
                        elif (MatParamID == 0x61):
                            pe.emissive1Name = TexName
                            if (pe.color1Name == ""):
                                pe.color1Name = TexName
                        elif (MatParamID == 0x62):
                            pe.prmName = TexName
                        elif (MatParamID == 0x63):
                            pe.envName = TexName
                        elif (MatParamID == 0x65):
                            pe.bakeName = TexName
                        elif (MatParamID == 0x66):
                            pe.color1Name = TexName
                        elif (MatParamID == 0x67):
                            pe.color2Name = TexName
                        elif (MatParamID == 0x6A):
                            pe.emissive2Name = TexName
                            if (pe.color2Name == ""):
                                pe.color2Name = TexName
                        elif (MatParamID == 0x133):
                            print("noise_for_warp")
                        else:
                            print("Unknown type (" + hex(MatParamID) + ") for " + TexName)

                        mt.seek(MatParamRet, 0)

                print("-----")
                Materials_array.append(pe)
                mt.seek(MATRet, 0)

            for m in range(MATCount):
                # Check and reuse existing same-name material, or create it if it doesn't already exist
                if (bpy.data.materials.find(Materials_array[m].materialName) > 0):
                    mat = bpy.data.materials[Materials_array[m].materialName]
                else:
                    mat = bpy.data.materials.new(Materials_array[m].materialName)
                mat.use_fake_user = True
                # Check and reuse existing same-name primary texture slot, or create it if it doesn't already exist
                if (Materials_array[m].color1Name != ""):
                    img = image_utils.load_image(Materials_array[m].color1Name + texture_ext, dirPath, place_holder=True, check_existing=True, force_reload=True)
                    img.alpha_mode = image_transparency
                    ma_wrap = node_shader_utils.PrincipledBSDFWrapper(mat, is_readonly=False)

                    ma_wrap.base_color_texture.image = img
                    ma_wrap.base_color_texture.texcoords = 'UV'

                # Check and reuse existing same-name primary texture slot, or create it if it doesn't already exist
                # if (Materials_array[m].color2Name != ""):
                #     if (bpy.data.textures.find(Materials_array[m].color2Name) > 0):
                #         altTex = bpy.data.textures[Materials_array[m].color2Name]
                #     else:
                #         altTex = bpy.data.textures.new(Materials_array[m].color2Name, type='IMAGE')

                #     altImg = image_utils.load_image(Materials_array[m].color2Name + texture_ext, dirPath, place_holder=True, check_existing=True, force_reload=True)
                #     altImg.alpha_mode = image_transparency
                #     altTex.image = altImg

                #     if (altTex.name not in mat.texture_slots):
                #         altSlot = mat.texture_slots.add()
                #         altSlot.texture = altTex
                #         altSlot.texture_coords = 'UV'

        print(Materials_array)

# Imports the skeleton
def importSkeleton(context, SKTName, create_rest_action):
    BoneCount = 0
    BoneParent_array = []
    BoneName_array = []
    global BoneTrsArray; BoneTrsArray = {}

    with open(SKTName, 'rb') as b:
        b.seek(0x10, 0)
        BoneCheck = struct.unpack('<L', b.read(4))[0]
        if (BoneCheck == 0x534B454C):
            SkelVerA = struct.unpack('<H', b.read(2))[0]
            SkelVerB = struct.unpack('<H', b.read(2))[0]
            b.seek(0x18, 0)
            BoneOffset = b.tell() + struct.unpack('<L', b.read(4))[0]; b.seek(0x04, 1)
            BoneCount = struct.unpack('<L', b.read(4))[0]; b.seek(0x04, 1)
            BoneMatrOffset = b.tell() + struct.unpack('<L', b.read(4))[0]; b.seek(0x04, 1)
            BoneMatrCount = struct.unpack('<L', b.read(4))[0]; b.seek(0x04, 1)
            BoneInvMatrOffset = b.tell() + struct.unpack('<L', b.read(4))[0]; b.seek(0x04, 1)
            BoneInvMatrCount = struct.unpack('<L', b.read(4))[0]; b.seek(0x04, 1)
            BoneRelMatrOffset = b.tell() + struct.unpack('<L', b.read(4))[0]; b.seek(0x04, 1)
            BoneRelMatrCount = struct.unpack('<L', b.read(4))[0]; b.seek(0x04, 1)
            BoneRelMatrInvOffset = b.tell() + struct.unpack('<L', b.read(4))[0]; b.seek(0x04, 1)
            BoneRelMatrInvCount = struct.unpack('<L', b.read(4))[0]; b.seek(0x04, 1)
            b.seek(BoneOffset, 0)

            for c in range(BoneCount):
                BoneNameOffset = b.tell() + struct.unpack('<L', b.read(4))[0]; b.seek(0x04, 1)
                BoneRet = b.tell()
                b.seek(BoneNameOffset, 0)
                BoneName = readVarLenString(b)
                b.seek(BoneRet, 0)
                BoneID = struct.unpack('<H', b.read(2))[0]
                BoneParent = struct.unpack('<H', b.read(2))[0]
                BoneUnk = struct.unpack('<L', b.read(4))[0]
                BoneParent_array.append(BoneParent)
                BoneName_array.append(BoneName)

            print("Total number of bones found: " + str(BoneCount))
            print(BoneParent_array)
            print(BoneName_array)

            b.seek(BoneMatrOffset, 0)
            # Before adding the bones, create a new armature and select it
            global skelName
            skelName = MODLName + "-armature"
            skel = bpy.data.objects.new(skelName, bpy.data.armatures.new(skelName))
            global armaName # Used in case another armature of the same name exists
            armaName = skel.data.name
            skel.rotation_mode = 'QUATERNION'
            skel.data.display_type = 'STICK'
            skel.show_in_front = True

            context.view_layer.active_layer_collection.collection.objects.link(skel)
            for i in bpy.context.selected_objects:
                i.select_set(False)
            skel.select_set(True)
            context.view_layer.objects.active = skel
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)

            for c in range(BoneCount):
                # Matrix format is [X, Y, Z, W]
                m11 = struct.unpack('<f', b.read(4))[0]; m12 = struct.unpack('<f', b.read(4))[0]; m13 = struct.unpack('<f', b.read(4))[0]; m14 = struct.unpack('<f', b.read(4))[0]
                m21 = struct.unpack('<f', b.read(4))[0]; m22 = struct.unpack('<f', b.read(4))[0]; m23 = struct.unpack('<f', b.read(4))[0]; m24 = struct.unpack('<f', b.read(4))[0]
                m31 = struct.unpack('<f', b.read(4))[0]; m32 = struct.unpack('<f', b.read(4))[0]; m33 = struct.unpack('<f', b.read(4))[0]; m34 = struct.unpack('<f', b.read(4))[0]
                m41 = struct.unpack('<f', b.read(4))[0]; m42 = struct.unpack('<f', b.read(4))[0]; m43 = struct.unpack('<f', b.read(4))[0]; m44 = struct.unpack('<f', b.read(4))[0]

                mr0 = [m11, m21, m31, m41]
                mr1 = [m12, m22, m32, m42]
                mr2 = [m13, m23, m33, m43]
                mr3 = [m14, m24, m34, m44]
                tfm = mathutils.Matrix([mr0, mr1, mr2, mr3])
                BoneTrsArray[BoneName_array[c]] = tfm
                # print("Matrix for " + BoneName_array[c] + ":\n" + str(tfm))
                # print(tfm.decompose())

                newBone = skel.data.edit_bones.new(BoneName_array[c])
                newBone.transform(tfm, scale=True, roll=False)

                # Bones must a be non-zero length, or Blender will eventually remove them
                newBone.tail = (newBone.head.x, newBone.head.y + 0.001, newBone.head.z)
                newBone.use_deform = True
                newBone.use_inherit_rotation = True
                newBone.use_inherit_scale = True

                # Store the original matrix rows as custom properties in bones so that they can be reused during animation transformation
                newBone['matrow0'] = mr0
                newBone['matrow1'] = mr1
                newBone['matrow2'] = mr2
                newBone['matrow3'] = mr3

            # Apply parents now that all bones exist
            for bc in range(BoneCount):
                currBone = skel.data.edit_bones[BoneName_array[bc]]
                if (BoneParent_array[bc] != 65535):
                    try:
                        currBone.parent = skel.data.edit_bones[BoneName_array[BoneParent_array[bc]]]
                    except:
                        # If parent bone can't be found
                        continue

            # Calculate the length for every bone, so that they will not be removed
            maxs = [0, 0, 0]
            mins = [0, 0, 0]
            for bone in BoneName_array:
                for i in range(3):
                        maxs[i] = max(maxs[i], BoneTrsArray[bone].to_translation()[i])
                        mins[i] = min(mins[i], BoneTrsArray[bone].to_translation()[i])
            # Get armature dimensions
            dimensions = []
            for i in range(3):
                dimensions.append(maxs[i] - mins[i])

            length = max(0.001, (dimensions[0] + dimensions[1] + dimensions[2]) / 600) # very small indeed, but usage of the stick visualization still lets the bones be reasonably visible

            for bone in skel.data.edit_bones:
                bone.matrix = BoneTrsArray[bone.name]
                bone.tail = bone.head + (bone.tail - bone.head).normalized() * length

            if create_rest_action:
                # Enter pose mode, and then create an action containing the rest pose if enabled
                bpy.ops.object.mode_set(mode='POSE', toggle=False)
                actionName = MODLName + "-rest"
                action = bpy.data.actions.new(actionName)
                action.pose_markers.new(actionName)

                try:
                    skel.animation_data.action
                except:
                    skel.animation_data_create()

                skel.animation_data.action = action
                skel.animation_data.action.use_fake_user = True
                context.scene.frame_current = context.scene.frame_start # Jump to beginning of new action

                for bone in skel.pose.bones:
                    bone.matrix_basis.identity()
                    bone.rotation_mode = 'QUATERNION'

                    # First, create position keyframes
                    skel.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                       (bone.name, "location"),
                                       frame=context.scene.frame_current,
                                       group=actionName)

                    # Next, create rotation keyframes
                    skel.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                       (bone.name, "rotation_quaternion"),
                                       frame=context.scene.frame_current,
                                       group=actionName)

                    # Last, create scale keyframes
                    skel.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                       (bone.name, "scale"),
                                       frame=context.scene.frame_current,
                                       group=actionName)

            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

# Imports the meshes
def importMeshes(context, MSHName, texture_ext, use_vertex_colors, use_uv_maps, allow_black):
    PolyGrp_array = []
    WeightGrp_array = []

    with open(MSHName, 'rb') as f:
        time_start = time.time()
        f.seek(0x10, 0)
        MSHCheck = struct.unpack('<L', f.read(4))[0]
        if (MSHCheck == 0x4D455348):
            MeshVerA = struct.unpack('<H', f.read(2))[0]
            MeshVerB = struct.unpack('<H', f.read(2))[0]
            f.seek(0x88, 0)
            PolyGrpInfOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            PolyGrpCount = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            UnkOffset1 = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            UnkCount1 = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            FaceBuffSizeB = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            VertBuffOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            UnkCount2 = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            FaceBuffOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            FaceBuffSize = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            WeightBuffOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            WeightCount = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)

            f.seek(PolyGrpInfOffset, 0)
            nameCounter = 0
            for g in range(PolyGrpCount):
                ge = PolygonGroupData()
                VisGrpNameOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x08, 1)
                Unk1 = struct.unpack('<L', f.read(4))[0]
                SingleBindNameOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                ge.verticeCount = struct.unpack('<L', f.read(4))[0]
                ge.facepointCount = struct.unpack('<L', f.read(4))[0]
                Unk2 = struct.unpack('<L', f.read(4))[0] # Always 3?
                ge.verticeStart = struct.unpack('<L', f.read(4))[0]
                ge.UVStart = struct.unpack('<L', f.read(4))[0]
                UnkOff1 = struct.unpack('<L', f.read(4))[0]
                Unk3 = struct.unpack('<L', f.read(4))[0] # Always 0?
                ge.verticeStride = struct.unpack('<L', f.read(4))[0]
                ge.UVStride = struct.unpack('<L', f.read(4))[0]
                Unk4 = struct.unpack('<L', f.read(4))[0] # Either 0 or 32
                Unk5 = struct.unpack('<L', f.read(4))[0] # Always 0
                ge.facepointStart = struct.unpack('<L', f.read(4))[0]
                Unk6 = struct.unpack('<L', f.read(4))[0] # Always 4
                ge.faceLongBit = struct.unpack('<L', f.read(4))[0] # Either 0 or 1
                Unk8 = struct.unpack('<L', f.read(4))[0] # Either 0 or 1
                SortPriority = struct.unpack('<L', f.read(4))[0]
                Unk9 = struct.unpack('<L', f.read(4))[0] # 0, 1, 256 or 257
                f.seek(0x64, 1) # A bunch of unknown float values.
                ge.bufferParamStart = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                ge.bufferParamCount = struct.unpack('<L', f.read(4))[0]
                Unk10 = struct.unpack('<L', f.read(4))[0] # Always 0
                PolyGrpRet = f.tell()
                f.seek(VisGrpNameOffset, 0)
                visGroupBuffer = readVarLenString(f)
                if (len(PolyGrp_array) > 0 and (PolyGrp_array[g - 1].visGroupName == visGroupBuffer or PolyGrp_array[g - 1].visGroupName[:-4] == visGroupBuffer)):
                    nameCounter += 1
                    ge.visGroupName = visGroupBuffer + str(nameCounter * .001)[1:]
                else:
                    ge.visGroupName = visGroupBuffer
                    nameCounter = 0
                f.seek(SingleBindNameOffset, 0)
                ge.singleBindName = readVarLenString(f)
                PolyGrp_array.append(ge)
                f.seek(PolyGrpRet, 0)

            print(PolyGrp_array)

            f.seek(VertBuffOffset, 0)
            VertOffStart = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            VertBuffSize = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            UVOffStart = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            UVBuffSize = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)

            f.seek(WeightBuffOffset, 0)
            nameCounter = 0
            for b in range(WeightCount):
                be = WeightGroupData()
                GrpNameOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                be.subGroupNum = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                be.weightInfMax = struct.unpack('<B', f.read(1))[0]
                be.weightFlag2 = struct.unpack('<B', f.read(1))[0]
                be.weightFlag3 = struct.unpack('<B', f.read(1))[0]
                be.weightFlag4 = struct.unpack('<B', f.read(1))[0]
                f.seek(0x04, 1)
                be.rigInfOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                be.rigInfCount = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                WeightRet = f.tell()
                f.seek(GrpNameOffset, 0)
                groupNameBuffer = readVarLenString(f)
                if (len(WeightGrp_array) > 0 and (WeightGrp_array[b - 1].groupName == groupNameBuffer or WeightGrp_array[b - 1].groupName[:-4] == groupNameBuffer)):
                    nameCounter += 1
                    be.groupName = groupNameBuffer + str(nameCounter * .001)[1:]
                else:
                    be.groupName = groupNameBuffer
                    nameCounter = 0
                WeightGrp_array.append(be)
                f.seek(WeightRet, 0)

            print(WeightGrp_array)

            # Repeats for every mesh group
            for p in range(PolyGrpCount):
                Vert_array = []
                Normal_array = []
                Color_array = {}
                Alpha_array = {}
                UV_array = {}
                Face_array = []
                Weight_array = []
                SingleBindID = 0

                # Add the meshes into Blender
                mesh =  bpy.data.meshes.new(PolyGrp_array[p].visGroupName)
                obj = bpy.data.objects.new(PolyGrp_array[p].visGroupName, mesh)
                obj.rotation_mode = 'QUATERNION'

                try:
                    if (len(MODLGrp_array[PolyGrp_array[p].visGroupName]) > 63):
                        mesh.materials.append(bpy.data.materials[MODLGrp_array[PolyGrp_array[p].visGroupName][:63]])
                    else:
                        mesh.materials.append(bpy.data.materials[MODLGrp_array[PolyGrp_array[p].visGroupName]])
                except:
                    # In case material cannot be found
                    continue
                mesh.use_auto_smooth = True

                try:
                    obj.parent = bpy.data.objects[armaName]
                    for bone in bpy.data.armatures[armaName].bones.values():
                        obj.vertex_groups.new(name=bone.name)
                    modifier = obj.modifiers.new(armaName, type="ARMATURE")
                    modifier.object = bpy.data.objects[armaName]
                except:
                    # If model does not have a skeleton
                    print(MODLName + " does not have an armature, skip parenting " + PolyGrp_array[p].visGroupName)

                # Begin reading mesh data
                f.seek(PolyGrp_array[p].bufferParamStart, 0)

                PosFmt = 0; NormFmt = 0; TanFmt = 0; ColorCount = 0; UVCount = 0

                for v in range(PolyGrp_array[p].bufferParamCount):
                    BuffParamType = struct.unpack('<L', f.read(4))[0]
                    BuffParamFmt = struct.unpack('<L', f.read(4))[0]
                    BuffParamSet = struct.unpack('<L', f.read(4))[0]
                    BuffParamOffset = struct.unpack('<L', f.read(4))[0]
                    BuffParamLayer = struct.unpack('<L', f.read(4))[0]
                    BuffParamUnk1 = struct.unpack('<L', f.read(4))[0] # always 0?
                    BuffParamStrOff1 = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                    BuffParamStrOff2 = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                    BuffParamUnk2 = struct.unpack('<L', f.read(4))[0] # always 1?
                    BuffParamUnk3 = struct.unpack('<L', f.read(4))[0] # always 0?
                    BuffParamRet = f.tell()
                    f.seek(BuffParamStrOff2, 0)
                    BuffNameOff = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 0)
                    f.seek(BuffNameOff, 0)
                    BuffName = readVarLenString(f)
                    if (BuffName == "Position0"):
                        PosFmt = BuffParamFmt
                    elif (BuffName == "Normal0"):
                        NormFmt = BuffParamFmt
                    elif (BuffName == "Tangent0"):
                        TanFmt = BuffParamFmt
                    elif (BuffName == "map1" or BuffName == "uvSet" or BuffName == "uvSet1" or BuffName == "uvSet2" or BuffName == "bake1"):
                        UV_array[UVCount] = []
                        UVCount += 1
                    elif (BuffName == "colorSet1" or BuffName == "colorSet2" or BuffName == "colorSet2_1" or BuffName == "colorSet2_2" or BuffName == "colorSet2_3" or BuffName == "colorSet3" or BuffName == "colorSet4" or BuffName == "colorSet5" or BuffName == "colorSet6" or BuffName == "colorSet7"):
                        Color_array[ColorCount] = []
                        Alpha_array[ColorCount] = []
                        ColorCount += 1

                    else:
                        raise RuntimeError("Unknown format!")
                    f.seek(BuffParamRet, 0)

                # Read vertice data
                print("Total number of vertices found: " + str(PolyGrp_array[p].verticeCount))
                f.seek(VertOffStart + PolyGrp_array[p].verticeStart, 0)

                print(PolyGrp_array[p].visGroupName + " Vert start: " + str(f.tell()))
                for v in range(PolyGrp_array[p].verticeCount):
                    if (PosFmt == 0):
                        vx = struct.unpack('<f', f.read(4))[0]
                        vy = struct.unpack('<f', f.read(4))[0]
                        vz = struct.unpack('<f', f.read(4))[0]
                        Vert_array.append([vx,vy,vz])
                    else:
                        print("Unknown position format!")
                    if (NormFmt == 5):
                        nx = decompressHalfFloat(f.read(2))
                        ny = decompressHalfFloat(f.read(2))
                        nz = decompressHalfFloat(f.read(2))
                        nq = decompressHalfFloat(f.read(2))
                        Normal_array.append([nx,ny,nz])
                    else:
                        print("Unknown normals format!")
                    if (TanFmt == 5):
                        tanx = decompressHalfFloat(f.read(2))
                        tany = decompressHalfFloat(f.read(2))
                        tanz = decompressHalfFloat(f.read(2))
                        tanq = decompressHalfFloat(f.read(2))
                    else:
                        print("Unknown tangents format!")

                print(PolyGrp_array[p].visGroupName + " Vert end: " + str(f.tell()))

                f.seek(UVOffStart + PolyGrp_array[p].UVStart, 0)
                print(PolyGrp_array[p].visGroupName + " UV start: " + str(f.tell()))
                for v in range(PolyGrp_array[p].verticeCount):
                    # Read UV map data if option is enabled
                    if (use_uv_maps and UVCount >= 1):
                        for uv in range(UVCount):
                            tu = decompressHalfFloat(f.read(2))
                            tv = (decompressHalfFloat(f.read(2)) * -1) + 1
                            UV_array[uv].append([tu, tv])

                    # Read vertex color data if option is enabled
                    if (use_vertex_colors and ColorCount >= 1):
                        for color in range(ColorCount):
                            colorr = float(struct.unpack('<B', f.read(1))[0]) / 128
                            colorg = float(struct.unpack('<B', f.read(1))[0]) / 128
                            colorb = float(struct.unpack('<B', f.read(1))[0]) / 128
                            colora = float(struct.unpack('<B', f.read(1))[0]) / 128
                            Color_array[color].append([colorr,colorg,colorb])
                            Alpha_array[color].append(colora)

                print(PolyGrp_array[p].visGroupName + " UV end: " + str(f.tell()))
                # Search for duplicate UV coordinates and make them unique so that Blender will not remove them
                if (len(UV_array) > 0):
                    for uvmap in UV_array.values():
                        for uvcoorda in range(0, len(uvmap) - 1):
                            count = uvcoorda
                            for uvcoordb in range(count + 1, len(uvmap)):
                                if (uvmap[uvcoordb] == uvmap[uvcoorda]):
                                    uvmap[uvcoordb][0] += 0.000000000000001
                                    uvmap[uvcoordb][1] += 0.000000000000001

                # Read face data
                f.seek(FaceBuffOffset + PolyGrp_array[p].facepointStart, 0)
                print(PolyGrp_array[p].visGroupName + " Face start: " + str(f.tell()))
                for fc in range(int(PolyGrp_array[p].facepointCount / 3)):
                    if (PolyGrp_array[p].faceLongBit == 0):
                        fa = struct.unpack('<H', f.read(2))[0] + 1
                        fb = struct.unpack('<H', f.read(2))[0] + 1
                        fc = struct.unpack('<H', f.read(2))[0] + 1
                        Face_array.append([fa,fb,fc])
                    elif (PolyGrp_array[p].faceLongBit == 1):
                        fa = struct.unpack('<L', f.read(4))[0] + 1
                        fb = struct.unpack('<L', f.read(4))[0] + 1
                        fc = struct.unpack('<L', f.read(4))[0] + 1
                        Face_array.append([fa,fb,fc])
                    else:
                        raise RuntimeError("Unknown face bit value!")

                print(PolyGrp_array[p].visGroupName + " Face end: " + str(f.tell()))

                if (PolyGrp_array[p].singleBindName != ""):
                    for b in range(len(bpy.data.armatures[armaName].bones)):
                        if (PolyGrp_array[p].singleBindName == bpy.data.armatures[armaName].bones[b].name):
                            SingleBindID = b

                    for b in range(len(Vert_array)):
                        Weight_array.append(WeightData([SingleBindID], [1.0]))
                else:
                    for b in range(len(Vert_array)):
                        Weight_array.append(WeightData([], []))

                    RigSet = 1
                    for b in range(len(WeightGrp_array)):
                            if (PolyGrp_array[p].visGroupName == WeightGrp_array[b].groupName):
                                RigSet = b
                                break
                    # Read vertice/weight group data
                    f.seek(WeightGrp_array[RigSet].rigInfOffset, 0)
                    print(PolyGrp_array[p].visGroupName + " Rig info start: " + str(f.tell()))

                    if (WeightGrp_array[RigSet].rigInfCount != 0):
                        for x in range(WeightGrp_array[RigSet].rigInfCount):
                            RigBoneNameOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                            RigBuffStart = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                            RigBuffSize = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                            RigRet = f.tell()
                            f.seek(RigBoneNameOffset, 0)
                            RigBoneName = readVarLenString(f)
                            f.seek(RigBuffStart, 0)
                            RigBoneID = 0
                            for b in range(len(bpy.data.armatures[armaName].bones)):
                                if (RigBoneName == bpy.data.armatures[armaName].bones[b].name):
                                    RigBoneID = b

                            if (RigBoneID == 0):
                                print(RigBoneName + " doesn't exist on " + PolyGrp_array[p].visGroupName + "! Transferring rigging to " + bpy.data.armatures[armaName].bones[1].name + ".")
                                RigBoneID = 1

                            for y in range(int(RigBuffSize / 0x06)):
                                RigVertID = struct.unpack('<H', f.read(2))[0]
                                RigValue = struct.unpack('<f', f.read(4))[0]
                                Weight_array[RigVertID].boneIDs.append(RigBoneID)
                                Weight_array[RigVertID].weights.append(RigValue)

                            f.seek(RigRet, 0)

                    else:
                        print(PolyGrp_array[p].visGroupName + " has no influences! Treating as a root singlebind instead.")
                        Weight_array = []
                        for b in range(len(Vert_array)):
                            Weight_array.append(WeightData([1], [1.0]))

                    # print(Weight_array)

                # Finally edit the mesh
                bm = bmesh.new()
                bm.from_mesh(mesh)

                weight_layer = bm.verts.layers.deform.new()

                for vertIndex, vert in enumerate(Vert_array):
                    bmv = bm.verts.new(vert)
                    bmv.normal = Normal_array[vertIndex]

                    for j in range(len(Weight_array[vertIndex].boneIDs)):
                        bmv[weight_layer][Weight_array[vertIndex].boneIDs[j]] =  Weight_array[vertIndex].weights[j]

                # Required after adding / removing vertices and before accessing them by index.
                bm.verts.ensure_lookup_table()
                # Required to actually retrieve the indices later on (or they stay -1).
                bm.verts.index_update()

                if (use_vertex_colors and ColorCount > 0):
                    colorLayers = []
                    alphaLayers = []
                    for c in range(len(Color_array)):
                        colorLayers.append(bm.loops.layers.color.new())
                        alphaLayers.append(bm.loops.layers.float.new())

                if (use_uv_maps and UVCount > 0):
                    uvLayers = []
                    # texLayers = []
                    for u in range(len(UV_array)):
                        uvLayers.append(bm.loops.layers.uv.new())
                        # texLayers.append(bm.faces.layers.tex.new())

                for face in range(len(Face_array)):
                    p0 = Face_array[face][0] - 1
                    p1 = Face_array[face][1] - 1
                    p2 = Face_array[face][2] - 1
                    try:
                        bmf = bm.faces.new([bm.verts[p0], bm.verts[p1], bm.verts[p2]])
                    except:
                        # Face already exists
                        continue

                for surface in bm.faces:
                    for loop in surface.loops:
                        # if (use_vertex_colors and ColorCount > 0):
                        #     for c in range(ColorCount):
                        #         if (Color_array[c][loop.vert.index] == [0.0, 0.0, 0.0] and not allow_black):
                        #             loop[colorLayers[c]] = [1.0, 1.0, 1.0]
                        #         else:
                        #             loop[colorLayers[c]] = Color_array[c][loop.vert.index]
                        #         loop[alphaLayers[c]] = Alpha_array[c][loop.vert.index]

                        if (use_uv_maps and UVCount > 0):
                            for u in range(UVCount):
                                loop[uvLayers[u]].uv = UV_array[u][loop.vert.index]

                for poly in mesh.polygons:
                    poly.use_smooth = True

                bm.to_mesh(mesh)
                bm.free()
                context.view_layer.active_layer_collection.collection.objects.link(obj)

                # Try to assign images to UV maps here
                if (use_uv_maps and UVCount > 0):
                    for id, uv_layer in enumerate(mesh.uv_layers):
                        for poly in uv_layer.data:
                            try:
                                poly.image = bpy.data.images[findUVImage(MODLGrp_array[PolyGrp_array[p].visGroupName], id) + texture_ext]
                            except:
                                # Image does not exist
                                continue

                # Apply matrix transformation to single-binding meshes
                if (PolyGrp_array[p].singleBindName != ""):
                    singlebone = PolyGrp_array[p].singleBindName
                    obj['singlebind'] = singlebone
                    obj.matrix_world = BoneTrsArray[singlebone]

                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                bpy.ops.object.shade_smooth()
                obj.data.update()

# ==== Import OPERATOR ====
from bpy_extras.io_utils import (ImportHelper)

class NUMDLB_Import_Operator(bpy.types.Operator, ImportHelper):
    """Loads a NUMDLB file and imports data referenced from it"""
    bl_idname = ("screen.numdlb_import")
    bl_label = ("NUMDLB Import")
    filename_ext = ".numdlb"
    filter_glob = bpy.props.StringProperty(default="*.numdlb", options={'HIDDEN'})

    image_transparency = bpy.props.EnumProperty(
            name="Image Alpha Type",
            description="Read image alpha channel to make images transparent",
            items=(("STRAIGHT", "Straight", "Straight, Store RGB and alpha channels separately with alpha acting as a mask, also known as unassociated alpha. Commonly used by image editing applications and file formats like PNG."),
                   ("PREMUL", "Premultiplied", "Premultiplied, Store RGB channels with alpha multiplied in, also known as associated alpha. The natural format for renders and used by file formats like OpenEXR."),
                   ("CHANNEL_PACKED", "Channel Packed", "Channel Packed, Different images are packed in the RGB and alpha channels, and they should not affect each other. Channel packing is commonly used by game engines to save memory."),
                   ("NONE", "None", "None, Ignore alpha channel from the file and make image fully opaque.")),
            default="STRAIGHT",
            )

    use_vertex_colors = bpy.props.BoolProperty(
            name="Vertex Colors",
            description="Import vertex color information to meshes",
            default=True,
            )

    use_uv_maps = bpy.props.BoolProperty(
            name="UV Maps",
            description="Import UV map information to meshes",
            default=True,
            )

    allow_black = bpy.props.BoolProperty(
            name="Black Vertex Colors",
            description="Allow black vertex coloring",
            default=False,
            )

    create_rest_action = bpy.props.BoolProperty(
            name="Backup Rest Pose",
            description="Create an action containing the rest pose",
            default=True,
            )

    auto_rotate = bpy.props.BoolProperty(
            name="Auto-Rotate Armature",
            description="Rotate the armature so that everything points up z-axis, instead of up y-axis",
            default=True,
            )

    texture_ext = bpy.props.EnumProperty(
            name="Texture File Extension",
            description="The file type to be associated with the texture names",
            items=((".bmp", "BMP", "Windows Bitmap"),
                   (".cin", "CIN", "Cineon"),
                   (".dpx", "DPX", "Digital Moving Picture Exchange"),
                   (".exr", "EXR", "OpenEXR"),
                   (".hdr", "HDR", "High Dynamic Range"),
                   (".jpg", "JPG", "Joint Photographic Expert Group"),
                   (".jpeg", "JPEG", "Joint Photographic Expert Group"),
                   (".jp2", "JP2", "Joint Photographic Expert Group 2000"),
                   (".j2k", "J2K", "Joint Photographic Expert Group 2000"),
                   (".png", "PNG", "Portable Network Graphics"),
                   (".rgb", "RGB", "Iris"),
                   (".tga", "TGA", "Targa"),
                   (".tif", "TIF", "Tagged Image File Format"),
                   (".tiff", "TIFF", "Tagged Image File Format")),
            default=".png",
            )

    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob",))
        time_start = time.time()
        getModelInfo(context, **keywords)
        context.view_layer.update()

        print("Done! Model import completed in " + str(round(time.time() - time_start, 4)) + " seconds.")
        return {"FINISHED"}

# Add to a menu
def menu_func_import(self, context):
    self.layout.operator(NUMDLB_Import_Operator.bl_idname, text="NUMDLB (.numdlb)")

def register():
    bpy.utils.register_class(NUMDLB_Import_Operator)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register
