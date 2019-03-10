#!BPY

"""
Name: 'Super Smash Bros. Ultimate Model Importer (.numdlb)...'
Blender: 270
Group: 'Import'
Tooltip: 'Import *.NUMDLB (.spm)'
"""

__author__ = ["Richard Qian (Worldblender), Random Talking Bush", "Ploaj"]
__url__ = ["https://gitlab.com/Worldblender/io_scene_numdlb"]
__version__ = "0.1"
__bpydoc__ = """\
"""

bl_info = {
    "name": "Super Smash Bros. Ultimate Model Importer",
    "description": "Imports data referenced by NUMDLB files (binary model format used by some games developed by Bandai-Namco)",
    "author": "Richard Qian (Worldblender), Random Talking Bush, Ploaj",
    "version": (0,1),
    "blender": (2, 7, 0),
    "api": 31236,
    "location": "File > Import",
    "warning": '', # used for warning icon and text in addons panel
    "wiki_url": "https://gitlab.com/Worldblender/io_scene_numdlb",
    "tracker_url": "https://gitlab.com/Worldblender/io_scene_numdlb/issues",
    "category": "Import-Export"}

import bmesh, bpy, bpy_extras, mathutils, os, struct, string, sys, time
from progress_report import ProgressReport, ProgressReportSubstep

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

class MatStruct:
    # struct MatStruct (MatName, MatColName, MatCol2Name, MatBakeName, MatNorName, MatEmiName, atEmi2Name, MatPrmName, MatEnvName)
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

class weight_data:
    # struct weight_data (boneids, weights)
    def __init__(self):
        self.boneIDs = []
        self.weights = []

    def __init__(self, boneIDs, weights):
        self.boneIDs = boneIDs
        self.weights = weights

    def __repr__(self):
        return "Bone IDs: " + str(self.boneIDs) + "\t| Weights: " + str(self.weights) + "\n"

class PolyGrpStruct:
    # struct PolyGrpStruct (VisGrpName, SingleBindName, FacepointCount, FacepointStart, FaceLongBit, VertCount, VertStart, VertStride, UVStart, UVStride, BuffParamStart, BuffParamCount)
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

class WeightGrpStruct:
    #struct WeightGrpStruct (GrpName, SubGroupNum, WeightInfMax, WeightFlag2, WeightFlag3, WeightFlag4, RigInfOffset, RigInfCount)
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

def findUVImageForMesh(matNameQuery, useUVMap2):
    for mat in Materials_array:
        if (mat.materialName == matNameQuery):
            if useUVMap2:
                return mat.color2Name
            else:
                return mat.color1Name
    return ""

def readVarLenString(file):
    nameBuffer = []
    while('\\' not in nameBuffer):
        nameBuffer.append(str(file.read(1))[2:3])
    del nameBuffer[-1]
    return ''.join(nameBuffer)

def getModelInfo(context, filepath, image_transparency=True, texture_ext=".png", up_axis='Y', use_vertex_colors=True, use_uv_maps=True, remove_doubles=False, connect_bones=False, auto_rotate=False):
    # Semi-global variables used by this function's hiearchy ; cleared every time this function runs
    global dirPath; dirPath = ""
    global MODLName; MODLName = ""
    global SKTName; SKTName = ""
    global MATName; MATName = ""
    global MSHName; MSHName = ""
    global skelName; skelName = ""
    global MODLGrp_array; MODLGrp_array = {}
    global Materials_array; Materials_array = []
    global BoneCount; BoneCount = 0
    global BoneArray; BoneArray = []
    global BoneFixArray; BoneFixArray = []
    global BoneTrsArray; BoneTrsArray = []
    global BoneParent_array; BoneParent_array = []
    global BoneName_array; BoneName_array = []
    global PolyGrp_array; PolyGrp_array = []
    global WeightGrp_array; WeightGrp_array = []
    
    if os.path.isfile(filepath):
        with open(filepath, 'rb') as md:
            dirPath = os.path.dirname(filepath)
            #struct MODLStruct (MSHGrpName, MSHMatName)

            md.seek(0x10, 0)
            # Reads the model file to find information about the other files
            MODLCheck = struct.unpack('<L', md.read(4))[0]
            if (MODLCheck == 0x4D4F444C):
                MODLVerA = struct.unpack('<H', md.read(2))[0] #unsigned
                MODLVerB = struct.unpack('<H', md.read(2))[0] #unsigned
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
                    # append MODLGrp_array (MODLStruct MSHGrpName:MSHGrpName MSHMatName:MSHMatName)
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
            importMaterials(context, MATName, image_transparency, texture_ext)
#        if os.path.isfile(SKTName):
#            importSkeleton(context, SKTName, connect_bones)
        if os.path.isfile(MSHName):
            importMeshes(context, MSHName, texture_ext, up_axis, use_vertex_colors, use_uv_maps, remove_doubles)
        
        # Rotate armature if option is enabled
        if auto_rotate:
            bpy.ops.object.select_all(action='TOGGLE')
            bpy.ops.object.select_pattern(pattern="*Armature*")
            bpy.ops.transform.rotate(value=math.radians(90), axis=(1, 0, 0), constraint_axis=(True, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
            bpy.ops.object.select_all(action='TOGGLE')
        
# Imports the materials
def importMaterials(context, MATName, image_transparency=True, texture_ext=".png"):
    with open(MATName, 'rb') as mt:
        # struct MatStruct (MatName, MatColName, MatCol2Name, MatBakeName, MatNorName, MatEmiName, atEmi2Name, MatPrmName, MatEnvName)

        mt.seek(0x10, 0)
        MATCheck = struct.unpack('<L', mt.read(4))[0]
        if (MATCheck == 0x4D41544C):
            MATVerA = struct.unpack('<H', mt.read(2))[0] #unsigned
            MATVerB = struct.unpack('<H', mt.read(2))[0] #unsigned
            MATHeadOff = mt.tell() + struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
            MATCount = struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
            mt.seek(MATHeadOff, 0)
            for m in range(MATCount):
                pe = MatStruct()
                MATNameOff = mt.tell() + struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
                MATParamGrpOff = mt.tell() + struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
                MATParamGrpCount = struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
                MATShdrNameOff = mt.tell() + struct.unpack('<L', mt.read(4))[0]; mt.seek(0x04, 1)
                MATRet = mt.tell()
                mt.seek(MATNameOff, 0)
                materialNameBuffer = []
                while('\\' not in materialNameBuffer):
                    materialNameBuffer.append(str(mt.read(1))[2:3])
                del materialNameBuffer[-1]
                pe.materialName = ''.join(materialNameBuffer)
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
                mat.specular_shader = 'PHONG'
                # Check and reuse existing same-name primary texture slot, or create it if it doesn't already exist
                if (Materials_array[m].color1Name != ""):
                    if (bpy.data.textures.find(Materials_array[m].color1Name) > 0):
                        
                        tex = bpy.data.textures[Materials_array[m].color1Name]
                    else:
                        tex = bpy.data.textures.new(Materials_array[m].color1Name, type='IMAGE')

                    imgPath = os.path.join(os.path.relpath(dirPath), Materials_array[m].color1Name + texture_ext)
                    if os.path.isfile(imgPath):
                        img = bpy.data.images.load(imgPath, check_existing=True)
                        img.use_alpha = image_transparency
                        tex.image = img
                        if (mat.texture_slots.find(tex.name) == -1):
                            slot = mat.texture_slots.add()
                            slot.texture = tex
                            slot.texture_coords = 'UV'
                # Check and reuse existing same-name primary texture slot, or create it if it doesn't already exist
                if (Materials_array[m].color2Name != ""):
                    if (bpy.data.textures.find(Materials_array[m].color2Name) > 0):
                        altTex = bpy.data.textures[Materials_array[m].color2Name]
                    else:
                        altTex = bpy.data.textures.new(Materials_array[m].color2Name, type='IMAGE')

                    altImgPath = os.path.join(os.path.relpath(dirPath), Materials_array[m].color2Name + texture_ext)
                    if os.path.isfile(altImgPath):
                        altImg = bpy.data.images.load(altImgPath, check_existing=True)
                        altImg.use_alpha = image_transparency
                        altTex.image = altImg
                        if (mat.texture_slots.find(altTex.name) == -1):
                            altSlot = mat.texture_slots.add()
                            altSlot.texture = altTex
                            altSlot.texture_coords = 'UV'

        print(Materials_array)

# Imports the skeleton
def importSkeleton(context, SKTName, connect_bones=False):
    with open(SKTName, 'rb') as b:
        b.seek(0x10, 0)
        BoneCheck = struct.unpack('<L', b.read(4))[0]
        if (BoneCheck == 0x534B454C):
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
                BoneParent = struct.unpack('<H', b.read(2))[0] + 1
                BoneUnk = struct.unpack('<L', b.read(4))[0]
                BoneParent_array.append(BoneParent)
                BoneName_array.append(BoneName)

            print("Total number of bones found: " + str(BoneCount))
            print(BoneParent_array)
            print(BoneName_array)

            b.seek(BoneMatrOffset, 0)
            # Before adding the bones, create a new armature and select it
            skelName = MODLName + "-armature"
            skel = bpy.data.objects.new(skelName, bpy.data.armatures.new(skelName))
            skel.data.draw_type = 'STICK'
            skel.show_x_ray = True
            bpy.context.scene.objects.link(skel)
            for i in bpy.context.selected_objects:
                i.select = False
            skel.select = True
            bpy.context.scene.objects.active = skel
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            for c in range(BoneCount):
                # Matrix format is [X, Y, Z, W]
                m11 = struct.unpack('<f', b.read(4))[0]; m12 = struct.unpack('<f', b.read(4))[0]; m13 = struct.unpack('<f', b.read(4))[0]; m14 = struct.unpack('<f', b.read(4))[0]
                m21 = struct.unpack('<f', b.read(4))[0]; m22 = struct.unpack('<f', b.read(4))[0]; m23 = struct.unpack('<f', b.read(4))[0]; m24 = struct.unpack('<f', b.read(4))[0]
                m31 = struct.unpack('<f', b.read(4))[0]; m32 = struct.unpack('<f', b.read(4))[0]; m33 = struct.unpack('<f', b.read(4))[0]; m34 = struct.unpack('<f', b.read(4))[0]
                m41 = struct.unpack('<f', b.read(4))[0]; m42 = struct.unpack('<f', b.read(4))[0]; m43 = struct.unpack('<f', b.read(4))[0]; m44 = struct.unpack('<f', b.read(4))[0]
                #tfm = matrix3 [m11,m12,m13] [m21,m22,m23] [m31,m32,m33] [m41,m42,m43] 
                tfm = [m11, m21, m31, m41, m12, m22, m32, m42, m13, m23, m33, m43, m14, m24, m34, m44]
                print("Matrix for " + BoneName_array[c] + ":\n" + str(tfm))
                newBone = skel.data.edit_bones.new(BoneName_array[c])
                # Advance to each column first, then row
                newBone.transform(tfm, scale=False, roll=False)
                if connect_bones:
                    newBone.use_connect = True
                else:
                    # Bones must a be non-zero length, or Blender will eventually remove them
                    newBone.tail = (0.0, 0.01, 0)
                newBone.use_deform = True
                newBone.use_inherit_rotation = True
                newBone.use_inherit_scale = True
                newBone.use_inherit_location = True
                if (BoneParent_array[c] != 0):
                    newBone.parent = BoneArray[BoneParent[c]]
                elif connect_bones:
                    # The parent bone, named "Trans", must a be non-zero length, or Blender will eventually remove it
                    newBone.tail = (0.0, 0.01, 0)
                # if (BoneParent[c] > c):
                #     BoneFixArray.append(c) # This thing again?
                BoneArray.append(newBone)
                BoneTrsArray.append(newBone.matrix)

            # for x in range(len(BoneFixArray)):
            #     select BoneArray[BoneFixArray[x]]
            #     $.parent = BoneArray[BoneParent_array[BoneFixArray[x]]]

# Imports the meshes
def importMeshes(context, MSHName, texture_ext=".png", up_axis='Y', use_vertex_colors=True, use_uv_maps=True, remove_doubles=False):
    with open(MSHName, 'rb') as f:
        time_start = time.time()
        # struct weight_data (boneids, weights)
        # struct PolyGrpStruct (VisGrpName, SingleBindName, FacepointCount, FacepointStart, FaceLongBit, VertCount, VertStart, VertStride, UVStart, UVStride, BuffParamStart, BuffParamCount)
        # struct WeightGrpStruct (GrpName, SubGroupNum, WeightInfMax, WeightFlag2, WeightFlag3, WeightFlag4, RigInfOffset, RigInfCount)

        f.seek(0x10, 0)
        MSHCheck = struct.unpack('<L', f.read(4))[0]
        if (MSHCheck == 0x4D455348):
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
                ge = PolyGrpStruct()
                VisGrpNameOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                f.seek(0x04, 1)
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
                print(ge.visGroupName + " unknowns: 1: " + str(Unk1) + "\t| Off1: " + str(UnkOff1) + "\t| 2: " + str(Unk2) + "\t| 3: " + str(Unk3) + "\t| 4: " + str(Unk4) + "\t| 5: " + str(Unk5) + "\t| 6: " + str(Unk6) + "\t| LongFace: " + str(ge.faceLongBit) + "\t| 8: " + str(Unk8) + "\t| Sort: " + str(SortPriority) + "\t| 9: " + str(Unk9) + "\t| 10: " + str(Unk10))
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
                be = WeightGrpStruct()
                GrpNameOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                be.subGroupNum = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                be.weightInfMax = struct.unpack('<B', f.read(1))[0] #unsigned
                be.weightFlag2 = struct.unpack('<B', f.read(1))[0] #unsigned
                be.weightFlag3 = struct.unpack('<B', f.read(1))[0] #unsigned
                be.weightFlag4 = struct.unpack('<B', f.read(1))[0] #unsigned
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
                Color_array = []; Color2_array = []; Color3_array = []; Color4_array = []; Color5_array = []
                Alpha_array = []; Alpha2_array = []; Alpha3_array = []; Alpha4_array = []; Alpha5_array = []
                UV_array = []; UV2_array = []; UV3_array = []; UV4_array = []; UV5_array = []
                Face_array = []
                Weight_array = []
                SingleBindID = 0

                f.seek(PolyGrp_array[p].bufferParamStart, 0)

                PosFmt = 0; NormFmt = 0; TanFmt = 0; ColorCount = 0; UVCount = 0

                for v in range(PolyGrp_array[p].bufferParamCount):
                    BuffParamType = struct.unpack('<L', f.read(4))[0]
                    BuffParamFmt = struct.unpack('<L', f.read(4))[0] + 1 # Adding one so that "0" counts as "none".
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
                        UVCount += 1
                    elif (BuffName == "colorSet1" or BuffName == "colorSet2" or BuffName == "colorSet2_1" or BuffName == "colorSet2_2" or BuffName == "colorSet2_3" or BuffName == "colorSet3" or BuffName == "colorSet4" or BuffName == "colorSet5" or BuffName == "colorSet6" or BuffName == "colorSet7"):
                        ColorCount += 1
                    else:
                        raise RuntimeError("Unknown format!")
                    f.seek(BuffParamRet, 0)
                # Read vertice data
                f.seek(VertOffStart + PolyGrp_array[p].verticeStart, 0)

                print(PolyGrp_array[p].visGroupName + " Vert start: " + str(f.tell()))
                for v in range(PolyGrp_array[p].verticeCount):
                    if (PosFmt == 1):
                        vx = struct.unpack('<f', f.read(4))[0]
                        vy = struct.unpack('<f', f.read(4))[0]
                        vz = struct.unpack('<f', f.read(4))[0]
                        if up_axis == 'Z':
                            Vert_array.append([vx,vz,vy]) # XZY
                        else:
                            Vert_array.append([vx,vy,vz]) # XYZ
                        
                    else:
                        print("Unknown position format!")
                    if (NormFmt == 6):
                        nx = decompressHalfFloat(f.read(2))
                        ny = decompressHalfFloat(f.read(2))
                        nz = decompressHalfFloat(f.read(2))
                        nq = decompressHalfFloat(f.read(2))
                        if up_axis == 'Z':
                            Normal_array.append([nx,nz,ny]) # XZY
                        else:
                            Normal_array.append([nx,ny,nz]) # XYZ
                        
                    else:
                        print("Unknown normals format!")
                    if (TanFmt == 6):
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
                    if use_uv_maps:
                        if (UVCount >= 1):
                            tu = decompressHalfFloat(f.read(2))
                            tv = (decompressHalfFloat(f.read(2)) * -1) + 1
                            UV_array.append([tu,tv])
                            if (UVCount >= 2):
                                tu2 = decompressHalfFloat(f.read(2))
                                tv2 = (decompressHalfFloat(f.read(2)) * -1) + 1
                                UV2_array.append([tu2,tv2])
                                if (UVCount >= 3):
                                    tu3 = decompressHalfFloat(f.read(2))
                                    tv3 = (decompressHalfFloat(f.read(2)) * -1) + 1
                                    UV3_array.append([tu3,tv3])
                                    if (UVCount >= 4):
                                        tu4 = decompressHalfFloat(f.read(2))
                                        tv4 = (decompressHalfFloat(f.read(2)) * -1) + 1
                                        UV4_array.append([tu4,tv4])
                                        if (UVCount >= 5):
                                            tu5 = decompressHalfFloat(f.read(2))
                                            tv5 = (decompressHalfFloat(f.read(2)) * -1) + 1
                                            UV5_array.append([tu5,tv5])
                                        if (UVCount >= 6):
                                            print("Importing more than 5 UV sets is not supported, not reading any more.")
                        else:
                            UV_array.append([0,0])
                    # Read vertex color data if option is enabled
                    if use_vertex_colors:
                        if (ColorCount >= 1):
                            colorr = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                            colorg = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                            colorb = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                            colora = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                            Color_array.append([colorr,colorg,colorb]); Alpha_array.append(colora)
                            if (ColorCount >= 2):
                                colorr2 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                                colorg2 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                                colorb2 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                                colora2 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                Color2_array.append([colorr2,colorg2,colorb2]); Alpha2_array.append(colora2)
                                if (ColorCount >= 3):
                                    colorr3 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                                    colorg3 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                                    colorb3 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                                    colora3 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                    Color3_array.append([colorr3,colorg3,colorb3]); Alpha3_array.append(colora3)
                                    if (ColorCount >= 4):
                                        colorr4 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                                        colorg4 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                                        colorb4 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                                        colora4 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                        Color4_array.append([colorr4,colorg4,colorb4]); Alpha4_array.append(colora4)
                                        if (ColorCount >= 5):
                                            colorr5 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                                            colorg5 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                                            colorb5 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned
                                            colora5 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                            Color5_array.append([colorr5,colorg5,colorb5]); Alpha5_array.append(colora5)
                                            if (ColorCount >= 6):
                                                print("Importing more than 5 vertex color sets is not supported, not reading any more.")
                        else:
                            Color_array.append([1.0,1.0,1.0])
                            Alpha_array.append(1.0)

                print(PolyGrp_array[p].visGroupName + " UV end: " + str(f.tell()))
                # Read face data
                f.seek(FaceBuffOffset + PolyGrp_array[p].facepointStart, 0)
                print(PolyGrp_array[p].visGroupName + " Face start: " + str(f.tell()))
                for fc in range(int(PolyGrp_array[p].facepointCount / 3)):
                    if (PolyGrp_array[p].faceLongBit == 0):
                        fa = struct.unpack('<H', f.read(2))[0] + 1 #unsigned + 1
                        fb = struct.unpack('<H', f.read(2))[0] + 1 #unsigned + 1
                        fc = struct.unpack('<H', f.read(2))[0] + 1 #unsigned + 1
                        if up_axis == 'Z':
                            Face_array.append([fa,fc,fb]) # XZY
                        else:
                            Face_array.append([fa,fb,fc]) # XYZ
                        

                    elif (PolyGrp_array[p].faceLongBit == 1):
                        fa = struct.unpack('<L', f.read(4))[0] + 1 #unsigned + 1
                        fb = struct.unpack('<L', f.read(4))[0] + 1 #unsigned + 1
                        fc = struct.unpack('<L', f.read(4))[0] + 1 #unsigned + 1
                        if up_axis == 'Z':
                            Face_array.append([fa,fc,fb]) # XZY
                        else:
                            Face_array.append([fa,fb,fc]) # XYZ
                        
                    else:
                        raise RuntimeError("Unknown face bit value!")

                print(PolyGrp_array[p].visGroupName + " Face end: " + str(f.tell()))

#                if (PolyGrp_array[p].singleBindName != ""):
#                    for b in range(len(BoneArray)):
#                        if (PolyGrp_array[p].singleBindName == BoneArray[b].name):
#                            SingleBindID = b
#
#                    for b in range(len(Vert_array)):
#                        Weight_array.append(weight_data([SingleBindID], [1.0]))
#                else:
#                    for b in range(len(Vert_array)):
#                        Weight_array.append(weight_data([0], [0]))
#
#                    RigSet = 1
#                    for b in range(len(WeightGrp_array)):
#                            if (PolyGrp_array[p].visGroupName == WeightGrp_array[b].groupName):
#                                RigSet = b
#                                # WeightGrp_array[b].groupName = "" # Dumb fix due to shared group names but split entries, prevents crashing.
#                                break
#                    # Read vertice/weight group data
#                    f.seek(WeightGrp_array[RigSet].rigInfOffset, 0)
#                    print(PolyGrp_array[p].visGroupName + " Rig info start: " + str(f.tell()))
#
#                    if (WeightGrp_array[RigSet].rigInfCount != 0):
#                        for x in range(WeightGrp_array[RigSet].rigInfCount):
#                            RigBoneNameOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
#                            RigBuffStart = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
#                            RigBuffSize = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
#                            RigRet = f.tell()
#                            f.seek(RigBoneNameOffset, 0)
#                            RigBoneName = readVarLenString(f)
#                            f.seek(RigBuffStart, 0)
#                            RigBoneID = 0
#                            for b in range(len(BoneArray)):
#                                if (RigBoneName == BoneArray[b].name):
#                                    RigBoneID = b
#
#                            if (RigBoneID == 0):
#                                print(RigBoneName + " doesn't exist on " + PolyGrp_array[p].visGroupName + "! Transferring rigging to " + BoneArray[1].name + ".")
#                                RigBoneID = 1
#
#                            for y in range(int(RigBuffSize / 0x06)):
#                                RigVertID = struct.unpack('<H', f.read(2))[0]
#                                RigValue = struct.unpack('<f', f.read(4))[0]
#                                Weight_array[RigVertID].boneIDs.append(RigBoneID)
#                                Weight_array[RigVertID].weights.append(RigValue)
#
#                            f.seek(RigRet, 0)
#
#                    else:
#                        print(PolyGrp_array[p].visGroupName + " has no influences! Treating as a root singlebind instead.")
#                        Weight_array = []
#                        for b in range(len(Vert_array)):
#                            Weight_array.append(weight_data([1], [1.0]))
#
#                    print(Weight_array)

                # Finally add the meshes into Blender
                mesh =  bpy.data.meshes.new(PolyGrp_array[p].visGroupName)
                obj = bpy.data.objects.new(PolyGrp_array[p].visGroupName, mesh)
                try:
                    if (len(MODLGrp_array[PolyGrp_array[p].visGroupName]) > 63):
                        mesh.materials.append(bpy.data.materials[MODLGrp_array[PolyGrp_array[p].visGroupName][:63]])
                    else:
                        mesh.materials.append(bpy.data.materials[MODLGrp_array[PolyGrp_array[p].visGroupName]])
                except:
                    # In case material cannot be found
                    continue
                mesh.use_auto_smooth = True
#                mesh.parent = bpy.data.objects[skelName]
#                
#                for bone in bpy.data.armatures[skelName].bones.values():
#                    mesh.vertex_groups.new(bone.name)
#                modifier = mesh.modifiers.new(skelName, type="ARMATURE")
#                modifier.object = skelName

                bm = bmesh.new()
                bm.from_mesh(mesh)
                
#                if (PolyGrp_array[p].singleBindName != ""):
#                        SingleBindID = 1
#                        for b in range(len(BoneName_array)):
#                            if (PolyGrp_array[p].singleBindName == BoneName_array[b]):
#                                SingleBindID = b
#                                break
#                        mesh.transform(BoneTrsArray[SingleBindID], shape_keys=False)
#                
#                if (BoneCount > 0):
#                    boneIDMap = []
#                    
#                    for i in range(len(BoneCount)):
#                        # maxbone = getnodebyname BoneArray[i].name
#                        if (i != BoneCount):
#                            pass# skinOps.addBone skinMod maxbone 0
#                        else:
#                            pass# skinOps.addBone skinMod maxbone 1
#                    
#                    # local numSkinBones = skinOps.GetNumberBones skinMod
#                    for bone in bpy.data.armatures[skelName].bones.values():
#                    # for i in range(len(numSkinBones)):
#                        # local boneName = skinOps.GetBoneName skinMod i 0
#                        for j in range(len(BoneCount)):
#                            if (bone.name == BoneArray[j].name):
#                                boneIDMap[j] = i
#                                j = BoneCount + 1
#                    
#                    # These fix broken rigging for 3DS Max 2015 and above.
#                    for i in range(len(Vert_array)):
#                        skinOps.SetVertexWeights skinMod i 1 1
#                        skinOps.unnormalizeVertex skinMod i true 
#                        skinOps.SetVertexWeights skinMod i 1 0
#                        skinOps.unnormalizeVertex skinMod i false
#                    )
#                
#                weight_layer = bm.verts.layers.deform.new()
                for vert in range(len(Vert_array)):
                    bmv = bm.verts.new(Vert_array[vert])
                    bmv.normal = Normal_array[vert]

#                    for w in Weight_array:
#                        bi = [] # bone index array
#                        wv = [] # weight value array
#
#                        for j in range(len(w.boneIDs)):
#                            boneid = w.boneIDs[j]
#                            weight = w.weights[j]
#                            bi.append(boneIDMap[boneid])
#                            wv.append(weight)
#
#                        bmv[weight_layer][bi] = wv
                # Required after adding / removing vertices and before accessing them
                # by index.
                bm.verts.ensure_lookup_table()
                # Required to actually retrieve the indices later on (or they stay -1).
                bm.verts.index_update()
                
                if (use_vertex_colors and ColorCount > 0):
                    if (len(Color_array) > 0):
                        color_layer = bm.loops.layers.color.new()
                    if (len(Color2_array) > 0):
                        color_layer_2 = bm.loops.layers.color.new()
                    if (len(Color3_array) > 0):
                        color_layer_3 = bm.loops.layers.color.new()
                    if (len(Color4_array) > 0):
                        color_layer_4 = bm.loops.layers.color.new()
                    if (len(Color5_array) > 0):
                        color_layer_5 = bm.loops.layers.color.new()
                
                if (use_uv_maps and UVCount > 0):
                    if (len(UV_array) > 0):
                        uv_layer = bm.loops.layers.uv.new()
                        tex_layer = bm.faces.layers.tex.new()
                    if (len(UV2_array) > 0):
                        uv_layer_2 = bm.loops.layers.uv.new()
                        tex_layer_2 = bm.faces.layers.tex.new()
                    if (len(UV3_array) > 0):
                        uv_layer_3 = bm.loops.layers.uv.new()
                        tex_layer_3 = bm.faces.layers.tex.new()
                    if (len(UV4_array) > 0):
                        uv_layer_4 = bm.loops.layers.uv.new()
                        tex_layer_4 = bm.faces.layers.tex.new()
                    if (len(UV5_array) > 0):
                        uv_layer_5 = bm.loops.layers.uv.new()
                        tex_layer_5 = bm.faces.layers.tex.new()

                for face in range(len(Face_array)):
                    p0 = Face_array[face][0] - 1
                    p1 = Face_array[face][1] - 1
                    p2 = Face_array[face][2] - 1
                    try:
                        bmf = bm.faces.new([bm.verts[p0], bm.verts[p1], bm.verts[p2]])
                    except:
                        # Face already exists
                        continue

                    if (use_uv_maps and UVCount > 0):
                            if (len(UV_array) > 0):
                                pass
                                #print(type(findUVImageForMesh(MODLGrp_array[PolyGrp_array[p].visGroupName], False) + texture_ext))
                                #face[tex_layer].image = findUVImageForMesh(MODLGrp_array[PolyGrp_array[p].visGroupName], False) + texture_ext
                            if (len(UV2_array) > 0):
                                pass
                                #print((findUVImageForMesh(MODLGrp_array[PolyGrp_array[p].visGroupName], True) + texture_ext))
                                #face[tex_layer_2].image = findUVImageForMesh(MODLGrp_array[PolyGrp_array[p].visGroupName], True) + texture_ext
                            """ Images can currently be linked only with the first 2 UV maps
                            if (len(UV3_array) > 0):
                                face[tex_layer_3].image = 
                            if (len(UV4_array) > 0):
                                face[tex_layer_4].image = 
                            if (len(UV5_array) > 0):
                                face[tex_layer_5].image = """
                
                for surface in bm.faces:
                    for loop in surface.loops:
                        if (use_vertex_colors and ColorCount > 0):
                            if (len(Color_array) > 0):
                                loop[color_layer] = Color_array[loop.vert.index] # + [Alpha_array[loop.vert.index]] Alpha can't be set here
                            if (len(Color2_array) > 0):
                                loop[color_layer_2] = Color2_array[loop.vert.index]
                            if (len(Color3_array) > 0):
                                loop[color_layer_3] = Color3_array[loop.vert.index]
                            if (len(Color4_array) > 0):
                                loop[color_layer_4] = Color4_array[loop.vert.index]
                            if (len(Color5_array) > 0):
                                loop[color_layer_5] = Color5_array[loop.vert.index]
                        if (use_uv_maps and UVCount > 0):
                            if (len(UV_array) > 0):
                                loop[uv_layer].uv = UV_array[loop.vert.index]
                            if (len(UV2_array) > 0):
                                loop[uv_layer_2].uv = UV2_array[loop.vert.index]
                            if (len(UV3_array) > 0):
                                loop[uv_layer_3].uv = UV3_array[loop.vert.index]
                            if (len(UV4_array) > 0):
                                loop[uv_layer_4].uv = UV4_array[loop.vert.index]
                            if (len(UV5_array) > 0):
                                loop[uv_layer_5].uv = UV5_array[loop.vert.index]

                for poly in mesh.polygons:
                    poly.use_smooth = True
                                 
                if remove_doubles:
                    bmesh.ops.remove_doubles(bm, verts = bm.verts)
                bm.to_mesh(mesh)
                bm.free()
                bpy.context.scene.objects.link(obj)

                bpy.ops.object.select_all(action="DESELECT")
                obj.select = True
                bpy.context.scene.objects.active = obj
                bpy.ops.object.shade_smooth()

        print("Done! Mesh import completed in " + str(round(time.time() - time_start)) + " seconds.")

# ==== Import OPERATOR ====
from bpy_extras.io_utils import (ImportHelper)

class NUMDLB_Import_Operator(bpy.types.Operator, ImportHelper):
    """Loads a NUMDLB file and imports data referenced from it"""
    bl_idname = ("screen.numdlb_import")
    bl_label = ("NUMDLB Import")
    filename_ext = ".numdlb"
    filter_glob = bpy.props.StringProperty(default="*.numdlb", options={'HIDDEN'})
    
    up_axis = bpy.props.EnumProperty(
            name="Up Axis",
            description="The axis all objects will point upwards with",
            items=(('Y', "Y", "Objects will appear sideways front and back"),
                   ('Z', "Z", "Objects will appear upright")),
            default='Y',
            )

    image_transparency = bpy.props.BoolProperty(
            name="Use Image Alpha",
            description="Read image alpha channel to make images transparent",
            default=True,
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

    remove_doubles = bpy.props.BoolProperty(
            name="Remove Doubles",
            description="Remove duplicate vertices",
            default=False,
            )

    connect_bones = bpy.props.BoolProperty(
            name="Connected Bones",
            description="Attach the head of every bone to their parent tail, except for the parent itself",
            default=False,
            )

    auto_rotate = bpy.props.BoolProperty(
            name="Auto-Rotate Armature",
            description="Rotate the armature so that everything points up z-axis, instead of up y-axis",
            default=True,
            )

    texture_ext = bpy.props.StringProperty(
            name="Texture File Extension",
            description="The file type to be associated with the texture names",
            default=".png",
            )

    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob", "auto_rotate"))
        getModelInfo(context, **keywords)

        context.scene.update()
        return {"FINISHED"}

# Add to a menu
def menu_func_import(self, context):
    self.layout.operator(NUMDLB_Import_Operator.bl_idname, text="NUMDLB (.numdlb)")

def register():
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.utils.register_module(__name__)

def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register
