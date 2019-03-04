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
    "description": "Imports NUMDLB files (binary model format used by some games developed by Bandai-Namco)",
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

class MODLStruct:
    # struct MODLStruct (MSHGrpName, MSHMatName)
    def __init__(self):
        self.meshGroupName = ""
        self.meshMaterialName = ""
    
    def __repr__(self):
        return "Mesh group name: " + str(self.meshGroupName) + " | Mesh material name: " + str(self.meshMaterialName) + "\n"

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
        return "Material name: " + str(self.materialName) + " | Color 1 name: " + str(self.color1Name) + " | Color 2 name: " + str(self.color2Name) + " | Bake name: " + str(self.bakeName) + " | Normal name: " + str(self.normalName) + " | Emissive 1 name: " + str(self.emissive1Name) + " | Emissive 2 name: " + str(self.emissive2Name) + " | PRM name: " + str(self.prmName) + " | Env name: " + str(self.envName) + "\n"

class weight_data:
    # struct weight_data (boneids, weights)
    def __init__(self):
        self.boneIDs = []
        self.weights = []

    def __repr__(self):
        return "Bone IDs:\n" + str(self.boneIDs) + "\nWeights:\n" + str(self.weights) + "\n"

class PolygrpStruct:
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
        return "Vis group name: " + str(self.visGroupName) + " | Single bind name: " + str(self.singleBindName) + " | Facepoint count: " + str(self.facepointCount) + " | Facepoint start: " + str(self.facepointStart) + " | Face long bit: " + str(self.faceLongBit) + " | Vertice count: " + str(self.verticeCount) + " | Vertice start " + str(self.verticeStart) + " | Vertice stride: " + str(self.verticeStride) + " | UV start: " + str(self.UVStart) + " | UV stride: " + str(self.UVStride) + " | Buffer parameter start: " + str(self.buffParamStart) + " | Buffer parameter count: " + str(self.buffParamCount) + "\n"

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
        return str(self.groupName) + " | Subgroup #: " + str(self.subGroupNum) + " | Weight info max: " + str(self.weightInfMax) + " | Weight flags" + str(self.weightFlag2) + ", " + str(self.weightFlag3) + ", " + str(self.weightFlag4) + " | Rig info offset: " + str(self.rigInfOffset) + " | Rig info count: " + str(self.rigInfCount) + "\n"

# Global variables used by all of the main functions
p = ""
SKTName = ""
MATName = ""
MSHName = ""
MODLGrp_array = []
Materials_array = []
BoneCount = 0
BoneArray = []
BoneFixArray = []
BoneTrsArray = []
BoneParent_array = []
BoneName_array = []
PolyGrp_array = []
WeightGrp_array = []

def getModelInfo(self, context, MDLName, print_debug_info=false):
    if os.path.isfile(MDLName):
        with open(MDLName, 'rb') as md:
            global p
            p = os.path.dirname(MDLName)
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
                # The next 3 names assume exactly "model" as the basename and the extension 6 characters long
                md.seek(SKTNameOff, 0)
                global SKTName
                SKTName = os.path.join(p, str(md.read(12))[2:14])
                md.seek(MATNameOff, 0)
                MATNameStrLen = struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                global MATName
                MATName = os.path.join(p, str(md.read(12))[2:14])
                md.seek(MSHNameOff, 0)
                global MSHName
                MSHName = os.path.join(p, str(md.read(12))[2:14]); md.seek(0x04, 1)
                md.seek(MSHDatOff, 0)
                global MODLGrp_array
                for g in range(MSHDatCount):
                    ge = MODLStruct()
                    MSHGrpNameOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                    MSHUnkNameOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                    MSHMatNameOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                    MSHRet = md.tell()
                    md.seek(MSHGrpNameOff, 0)
                    groupNameBuffer = []
                    while('\\' not in groupNameBuffer):
                        groupNameBuffer.append(str(md.read(1))[2:3])
                    del groupNameBuffer[-1]
                    ge.meshGroupName = ''.join(groupNameBuffer)
                    md.seek(MSHMatNameOff, 0)
                    materialNameBuffer = []
                    while('\\' not in materialNameBuffer):
                        materialNameBuffer.append(str(md.read(1))[2:3])
                    del materialNameBuffer[-1]
                    ge.meshMaterialName = ''.join(materialNameBuffer)
                    # append MODLGrp_array (MODLStruct MSHGrpName:MSHGrpName MSHMatName:MSHMatName)
                    MODLGrp_array.append(ge)
                    md.seek(MSHRet, 0)
                if print_debug_info:
                    print(MODLGrp_array)
        
# Imports the materials
def importMaterials(self, context, MATName, texture_ext=".png", print_debug_info=false):
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
            global Materials_array
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
                        textureNameBuffer = []
                        while('\\' not in textureNameBuffer):
                            textureNameBuffer.append(str(mt.read(1))[2:3])
                        del textureNameBuffer[-1]
                        TexName = ''.join(textureNameBuffer)
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
                            if print_debug_info:
                                print("Unknown type (" + hex(MatParamID) + ") for " + TexName)

                        mt.seek(MatParamRet, 0)

                print("-----")
                Materials_array.append(pe)
                mt.seek(MATRet, 0)

            for m in range(MATCount):
                if (bpy.data.materials.find(Materials_array[m].materialName) == -1):
                    mat = bpy.data.materials.new(Materials_array[m].materialName)
                if (bpy.data.textures.find(Materials_array[m].color1Name) == -1):
                    tex = bpy.data.textures.new(Materials_array[m].color1Name, IMAGE)
                img = bpy.data.images.load(os.path.join(p, Materials_array[m].color1Name, texture_ext), check_existing=True)
                tex.image = im
                if (mat.texture_slots.find(tex.name) == -1):
                    slot = mat.texture_slots.add()
                    slot.texture = tex
                    slot.texture_coords = 'UV'
            
        if print_debug_info:
            print(Materials_array)

# Imports the skeleton
def importSkeleton(self, context, SKTName, print_debug_info=false):
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
                boneNameBuffer = []
                while('\\' not in boneNameBuffer):
                    boneNameBuffer.append(str(b.read(1))[2:3])
                del boneNameBuffer[-1]
                BoneName = ''.join(boneNameBuffer)
                b.seek(BoneRet, 0)
                BoneID = struct.unpack('<H', b.read(2))[0]
                BoneParent = struct.unpack('<H', b.read(2))[0] + 1
                BoneUnk = struct.unpack('<L', b.read(4))[0]
                BoneParent_array.append(BoneParent)
                BoneName_array.append(BoneName)

            if print_debug_info:
                print(BoneParent_array)
                print(BoneName_array)

            b.seek(BoneMatrOffset, 0)

            for c in range(BoneCount):
                m11 = ('<f', b.read(4))[0]; m12 = ('<f', b.read(4))[0]; m13 = ('<f', b.read(4))[0]; m14 = ('<f', b.read(4))[0]
                m21 = ('<f', b.read(4))[0]; m22 = ('<f', b.read(4))[0]; m23 = ('<f', b.read(4))[0]; m24 = ('<f', b.read(4))[0]
                m31 = ('<f', b.read(4))[0]; m32 = ('<f', b.read(4))[0]; m33 = ('<f', b.read(4))[0]; m34 = ('<f', b.read(4))[0]
                m41 = ('<f', b.read(4))[0]; m42 = ('<f', b.read(4))[0]; m43 = ('<f', b.read(4))[0]; m44 = ('<f', b.read(4))[0]
                tfm = matrix3 [m11,m12,m13] [m21,m22,m23] [m31,m32,m33] [m41,m42,m43]
                newBone = bonesys.createbone   \
                    tfm.row4   \
                    (tfm.row4 + 0.01 * (normalize tfm.row1)) \
                    (normalize tfm.row3)
                    BoneName = BoneName_array[c]
                    BoneParent = BoneParent_array[c]
                    newBone.name = BoneName
                    newBone.width  = 0.01
                    newBone.height = 0.01
                    newBone.transform = tfm
                    newBone.setBoneEnable false 0
                    newBone.wirecolor = yellow
                    newBone.showlinks = true
                    newBone.pos.controller      = TCB_position ()
                    newBone.rotation.controller = TCB_rotation ()
                    if (BoneParent != 0) then
                    newBone.parent = BoneArray[(BoneParent)]
                    if BoneParent > c do(append BoneFixArray c) # This thing again?
                    append BoneArray newBone
                    append BoneTrsArray newBone.transform
            )
            for x in range(len(BoneFixArray)):
                select BoneArray[BoneFixArray[x]]
                $.parent = BoneArray[BoneParent_array[BoneFixArray[x]]]
            )
        )
    )

# Imports the meshes
def importMeshes(self, context, MSHName, use_vertex_colors=true, print_debug_info=false):
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
            for g in range(PolyGrpCount):
                VisGrpNameOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                f.seek(0x04, 1)
                Unk1 = struct.unpack('<L', f.read(4))[0]
                SingleBindNameOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                VertCount = struct.unpack('<L', f.read(4))[0]
                FacepointCount = struct.unpack('<L', f.read(4))[0]
                Unk2 = struct.unpack('<L', f.read(4))[0] # Always 3?
                VertStart = struct.unpack('<L', f.read(4))[0]
                UVStart = struct.unpack('<L', f.read(4))[0]
                UnkOff1 = struct.unpack('<L', f.read(4))[0]
                Unk3 = struct.unpack('<L', f.read(4))[0] # Always 0?
                VertStride = struct.unpack('<L', f.read(4))[0]
                UVStride = struct.unpack('<L', f.read(4))[0]
                Unk4 = struct.unpack('<L', f.read(4))[0] # Either 0 or 32
                Unk5 = struct.unpack('<L', f.read(4))[0] # Always 0
                FacepointStart = struct.unpack('<L', f.read(4))[0]
                Unk6 = struct.unpack('<L', f.read(4))[0] # Always 4
                FaceLongBit = struct.unpack('<L', f.read(4))[0] # Either 0 or 1
                Unk8 = struct.unpack('<L', f.read(4))[0] # Either 0 or 1
                SortPriority = struct.unpack('<L', f.read(4))[0]
                Unk9 = struct.unpack('<L', f.read(4))[0] # 0, 1, 256 or 257
                f.seek(0x64, 1) # A bunch of unknown float values.
                BuffParamStart = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                BuffParamCount = struct.unpack('<L', f.read(4))[0]
                Unk10 = struct.unpack('<L', f.read(4))[0] # Always 0
                PolyGrpRet = f.tell()
                f.seek(VisGrpNameOffset, 0)
                visGroupBuffer = []
                while('\\' not in visGroupBuffer):
                    visGroupBuffer.append(str(f.read(1))[2:3])
                del visGroupBuffer[-1]
                VisGrpName = ''.join(visGroupBuffer)
                f.seek(SingleBindNameOffset, 0)
                oneBindNameBuffer = []
                while('\\' not in oneBindNameBuffer):
                    oneBindNameBuffer.append(str(f.read(1))[2:3])
                del OneBindNameBuffer[-1]
                SingleBindName = ''.join(oneBindNameBuffer)
                # PolyGrp_array.append(PolyGrpStruct VisGrpName:VisGrpName SingleBindName:SingleBindName FacepointCount:FacepointCount FacepointStart:FacepointStart FaceLongBit:FaceLongBit VertCount:VertCount VertStart:VertStart VertStride:VertStride UVStart:UVStart UVStride:UVStride BuffParamStart:BuffParamStart BuffParamCount:BuffParamCount)
                if print_debug_info:
                    print(VisGrpName + " unknowns: 1: " + Unk1 + " | Off1: " + UnkOff1 + " | 2: " + Unk2 + " | 3: " + Unk3 + " | 4: " + Unk4 + " | 5: " + Unk5 + " | 6: " + Unk6 + " | LongFace: " + FaceLongBit + " | 8: " + Unk8 + " | Sort: " + SortPriority + " | 9: " + Unk9 + " | 10: " + Unk10)
                f.seek(PolyGrpRet, 0)
            )
            if print_debug_info:
                print(PolyGrp_array)

            f.seek(VertBuffOffset, 0)
            VertOffStart = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            VertBuffSize = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            UVOffStart = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            UVBuffSize = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)

            f.seek(WeightBuffOffset, 0)

            for b in range(WeightCount):
                GrpNameOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                SubGroupNum = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                WeightInfMax = struct.unpack('<B', spm.read(1))[0] #unsigned
                WeightFlag2 = struct.unpack('<B', spm.read(1))[0] #unsigned
                WeightFlag3 = struct.unpack('<B', spm.read(1))[0] #unsigned
                WeightFlag4 = struct.unpack('<B', spm.read(1))[0] #unsigned
                f.seek(0x04, 1)
                RigInfOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                RigInfCount = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                WeightRet = f.tell()
                f.seek(GrpNameOffset, 0)
                groupNameBuffer = []
                while('\\' not in groupNameBuffer):
                    groupNameBuffer.append(str(f.read(1))[2:3])
                del groupNameBuffer[-1]
                GrpName = ''.join(groupNameBuffer)
                # WeightGrp_array.append(WeightGrpStruct GrpName:GrpName SubGroupNum:SubGroupNum WeightInfMax:WeightInfMax WeightFlag2:WeightFlag2 WeightFlag3:WeightFlag3 WeightFlag4:WeightFlag4 RigInfOffset:RigInfOffset RigInfCount:RigInfCount)
                f.seek(WeightRet, 0)

            if print_debug_info:
                print(WeightGrp_array)

            for p in range(PolyGrpCount):
                Vert_array = []
                Normal_array = []
                Color_array = []; Color2_array = []; Color3_array = []; Color4_array = []; Color5_array = []
                Alpha_array = []; Alpha2_array = []; Alpha3_array = []; Alpha4_array = []; Alpha5_array = []
                UV_array = []; UV2_array = []; UV3_array = []; UV4_array = []; UV5_array = []
                Face_array = []
                Weight_array = []
                SingleBindID = 0

                f.seek(PolyGrp_array[p].BuffParamStart, 0)

                PosFmt = 0; NormFmt = 0; TanFmt = 0; ColorCount = 0; UVCount = 0

                for v = 1 to PolyGrp_array[p].BuffParamCount do(
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
                    bufferNameBuffer = []
                    while('\\' not in bufferNameBuffer):
                        bufferNameBuffer.append(str(f.read(1))[2:3])
                    del bufferNameBuffer[-1]
                    BuffName = ''.join(bufferNameBuffer)
                    case BuffName of(
                        default: (throw ("Unknown format!"))
                        "Position0":(PosFmt = BuffParamFmt)
                        "Normal0":(NormFmt = BuffParamFmt)
                        "Tangent0":(TanFmt = BuffParamFmt)
                        "map1":(UVCount = UVCount + 1)
                        "uvSet":(UVCount = UVCount + 1)
                        "uvSet1":(UVCount = UVCount + 1)
                        "uvSet2":(UVCount = UVCount + 1)
                        "bake1":(UVCount = UVCount + 1)
                        "colorSet1":(ColorCount = ColorCount + 1)
                        "colorSet2":(ColorCount = ColorCount + 1)
                        "colorSet2_1":(ColorCount = ColorCount + 1)
                        "colorSet2_2":(ColorCount = ColorCount + 1)
                        "colorSet2_3":(ColorCount = ColorCount + 1)
                        "colorSet3":(ColorCount = ColorCount + 1)
                        "colorSet4":(ColorCount = ColorCount + 1)
                        "colorSet5":(ColorCount = ColorCount + 1)
                        "colorSet6":(ColorCount = ColorCount + 1)
                        "colorSet7":(ColorCount = ColorCount + 1)
                    )
                    f.seek(BuffParamRet, 0)
                )

                f.seek(VertOffStart + PolyGrp_array[p].VertStart, 0)

                if print_debug_info:
                    print("Vert start: " + f.tell())
                for v = 1 to PolyGrp_array[p].VertCount do(
                    case PosFmt of(
                            default: ("Unknown position format!")
                            1:(
                                    vx = ('<f', f.read(4))[0]
                                    vy = ('<f', f.read(4))[0]
                                    vz = ('<f', f.read(4))[0]
                                    append Vert_array [vx,vy,vz]
                            )
                    )
                    case NormFmt of(
                            default: ("Unknown normals format!")
                            6:(
                                    nx = decompressHalfFloat(f.read(2)) * 2 
                                    ny = decompressHalfFloat(f.read(2)) * 2
                                    nz = decompressHalfFloat(f.read(2)) * 2
                                    nq = decompressHalfFloat(f.read(2)) * 2
                                    append Normal_array [nx,ny,nz]
                            )
                    )
                    case TanFmt of(
                            default: ("Unknown tangents format!")
                            6:(
                                    tanx = decompressHalfFloat(f.read(2)) * 2
                                    tany = decompressHalfFloat(f.read(2)) * 2
                                    tanz = decompressHalfFloat(f.read(2)) * 2
                                    tanq = decompressHalfFloat(f.read(2)) * 2
                            )
                    )
                )
                if print_debug_info:
                    print("Vert end: " + f.tell())

                f.seek(UVOffStart + PolyGrp_array[p].UVStart, 0)

                if print_debug_info:
                    print("UV start: " + f.tell())
                for v = 1 to PolyGrp_array[p].VertCount do(
                    case UVCount of(
                        default: (throw ("More than 5 UV sets, crashing gracefully."))
                        0:(
                                append UV_array [0,0,0]
                        )
                        1:(
                                tu = (decompressHalfFloat(f.read(2)) * 2)
                                tv = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                append UV_array [tu,tv,0]
                        )
                        2:(
                                tu = (decompressHalfFloat(f.read(2)) * 2)
                                tv = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                tu2 = (decompressHalfFloat(f.read(2)) * 2)
                                tv2 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                append UV_array [tu,tv,0]
                                append UV2_array [tu2,tv2,0]
                        )
                        3:(
                                tu = (decompressHalfFloat(f.read(2)) * 2)
                                tv = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                tu2 = (decompressHalfFloat(f.read(2)) * 2)
                                tv2 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                tu3 = (decompressHalfFloat(f.read(2)) * 2)
                                tv3 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                append UV_array [tu,tv,0]
                                append UV2_array [tu2,tv2,0]
                                append UV3_array [tu3,tv3,0]
                        )
                        4:(
                                tu = (decompressHalfFloat(f.read(2)) * 2)
                                tv = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                tu2 = (decompressHalfFloat(f.read(2)) * 2)
                                tv2 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                tu3 = (decompressHalfFloat(f.read(2)) * 2)
                                tv3 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                tu4 = (decompressHalfFloat(f.read(2)) * 2)
                                tv4 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                append UV_array [tu,tv,0]
                                append UV2_array [tu2,tv2,0]
                                append UV3_array [tu3,tv3,0]
                                append UV4_array [tu4,tv4,0]
                        )
                        5:(
                                tu = (decompressHalfFloat(f.read(2)) * 2)
                                tv = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                tu2 = (decompressHalfFloat(f.read(2)) * 2)
                                tv2 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                tu3 = (decompressHalfFloat(f.read(2)) * 2)
                                tv3 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                tu4 = (decompressHalfFloat(f.read(2)) * 2)
                                tv4 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                tu5 = (decompressHalfFloat(f.read(2)) * 2)
                                tv5 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                                append UV_array [tu,tv,0]
                                append UV2_array [tu2,tv2,0]
                                append UV3_array [tu3,tv3,0]
                                append UV4_array [tu4,tv4,0]
                                append UV5_array [tu5,tv5,0]
                        )
                    )
                    case ColorCount of(
                        default: (throw ("More than 5 color sets, crashing gracefully."))
                        0:(
                                append Color_array [128,128,128]
                                append Alpha_array 1
                        )
                        1:(
                                colorr = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                append Color_array [colorr,colorg,colorb]; append Alpha_array colora
                        )
                        2:(
                                colorr = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                colorr2 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg2 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb2 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora2 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                append Color_array [colorr,colorg,colorb]; append Alpha_array colora
                                append Color2_array [colorr2,colorg2,colorb2]; append Alpha2_array colora2
                        )
                        3:(
                                colorr = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                colorr2 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg2 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb2 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora2 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                colorr3 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg3 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb3 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora3 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                append Color_array [colorr,colorg,colorb]; append Alpha_array colora
                                append Color2_array [colorr2,colorg2,colorb2]; append Alpha2_array colora2
                                append Color3_array [colorr3,colorg3,colorb3]; append Alpha3_array colora3
                        )
                        4:(
                                colorr = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                colorr2 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg2 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb2 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora2 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                colorr3 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg3 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb3 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora3 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                colorr4 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg4 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb4 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora4 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                append Color_array [colorr,colorg,colorb]; append Alpha_array colora
                                append Color2_array [colorr2,colorg2,colorb2]; append Alpha2_array colora2
                                append Color3_array [colorr3,colorg3,colorb3]; append Alpha3_array colora3
                                append Color4_array [colorr4,colorg4,colorb4]; append Alpha4_array colora4
                        )
                        5:(
                                colorr = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                colorr2 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg2 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb2 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora2 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                colorr3 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg3 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb3 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora3 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                colorr4 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg4 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb4 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora4 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                colorr5 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorg5 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colorb5 = struct.unpack('<B', f.read(1))[0] #unsigned
                                colora5 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                                append Color_array [colorr,colorg,colorb]; append Alpha_array colora
                                append Color2_array [colorr2,colorg2,colorb2]; append Alpha2_array colora2
                                append Color3_array [colorr3,colorg3,colorb3]; append Alpha3_array colora3
                                append Color4_array [colorr4,colorg4,colorb4]; append Alpha4_array colora4
                                append Color5_array [colorr5,colorg5,colorb5]; append Alpha5_array colora5
                        )
                    )
                )
                if print_debug_info:
                    print("UV end: " + f.tell())

                f.seek(FaceBuffOffset + PolyGrp_array[p].FacepointStart, 0)
                if print_debug_info:
                    print("Face start: " + f.tell())
                for fc = 1 to (PolyGrp_array[p].FacepointCount / 3) do(
                    case PolyGrp_array[p].FaceLongBit of(
                        default:(throw("Unknown face bit value!"))
                        0:(
                            fa = ('<H', f.read(2))[0] + 1 #unsigned + 1
                            fb = ('<H', f.read(2))[0] + 1 #unsigned + 1
                            fc = ('<H', f.read(2))[0] + 1 #unsigned + 1
                            Face_array.append([fa,fb,fc])
                        )
                        1:(
                            fa = struct.unpack('<L', f.read(4))[0] + 1 #unsigned + 1
                            fb = struct.unpack('<L', f.read(4))[0] + 1 #unsigned + 1
                            fc = struct.unpack('<L', f.read(4))[0] + 1 #unsigned + 1
                            Face_array.append([fa,fb,fc])
                        )
                    )
                )
                if print_debug_info:
                    print("Face end: " + f.tell())

                if PolyGrp_array[p].SingleBindName != "" then (
                    for b = 1 to BoneArray.count do(
                            if PolyGrp_array[p].SingleBindName == BoneArray[b].name do(
                                    SingleBindID = b
                            )
                    )
                    for b = 1 to Vert_array.count do(
                            append Weight_array (weight_data boneids:#(SingleBindID) weights:#(1.0))
                    )
                ) else (
                    for b = 1 to Vert_array.count do(
                            append Weight_array (weight_data boneids:[] weights:[])
                    )
                    RigSet = 1
                    for b = 1 to WeightGrp_array.count do(
                            if PolyGrp_array[p].VisGrpName == WeightGrp_array[b].GrpName do(
                                    RigSet = b
                                    WeightGrp_array[b].GrpName = "" # Dumb fix due to shared group names but split entries, prevents crashing.
                                    exit
                            )
                    )

                    f.seek(WeightGrp_array[RigSet].RigInfOffset, 0)
                    if print_debug_info:
                        print("Rig info start: " + f.tell())

                    if WeightGrp_array[RigSet].RigInfCount != 0 then (
                        for x = 1 to WeightGrp_array[RigSet].RigInfCount do(
                            RigBoneNameOffset = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                            RigBuffStart = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                            RigBuffSize = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
                            RigRet = f.tell()
                            f.seek(RigBoneNameOffset, 0)
                            rigBoneNameBuffer = []
                            while('\\' not in rigBoneNameBuffer):
                                rigBoneNameBuffer.append(str(f.read(1))[2:3])
                            del rigBoneNameBuffer[-1]
                            RigBoneName = ''.join(rigBoneNameBuffer)
                            f.seek(RigBuffStart, 0)
                            RigBoneID = 0
                            for b = 1 to BoneArray.count do(
                                    if RigBoneName == BoneArray[b].name do(
                                            RigBoneID = b
                                    )
                            )
                            if RigBoneID == 0 do(
                                    print (RigBoneName + " doesn't exist on " + PolyGrp_array[p].VisGrpName + "! Transferring rigging to " + BoneArray[1].name + ".")
                                    RigBoneID = 1
                            )
                            for y = 1 to (RigBuffSize / 0x06) do(
                                    RigVertID = ('<H', f.read(2))[0] + 1
                                    RigValue = ('<f', f.read(4))[0]
                                    append Weight_array[RigVertID].boneids RigBoneID
                                    append Weight_array[RigVertID].weights RigValue
                            )
                            f.seek(RigRet, 0)
                        ) 
                    ) else (
                        print (PolyGrp_array[p].VisGrpName + " has no influences! Treating as a root singlebind instead.")
                        Weight_array = []
                        for b = 1 to Vert_array.count do(
                                append Weight_array (weight_data boneids:#(1) weights:#(1.0))
                        )
                    )
                )

                MatID = 1
                for b = 1 to Materials_array.count do(
                        if MODLGrp_array[p].MSHMatName == Materials_array[b].MatName do(
                                MatID = b
                                exit
                        )
                )
                msh = mesh vertices:Vert_array faces:Face_array
                msh.numTVerts = Vert_array.count
                if PolyGrp_array[p].SingleBindName != "" do(
                        SingleBindID = 1
                        for b = 1 to BoneName_array.count do(
                                if PolyGrp_array[p].SingleBindName == BoneName_array[b] do(
                                        SingleBindID = b
                                        exit
                                )
                        )
                        msh.transform = BoneTrsArray[SingleBindID]
                )
                if (use_vertex_colors == True):
                    setNumCPVVerts msh msh.numTVerts
                    setCVertMode msh true
                    setShadeCVerts msh true

                defaultVCFaces msh
                buildTVFaces msh
                msh.name = (PolyGrp_array[p].VisGrpName as string)
                msh.material = multimat
                for j = 1 to UV_array.count do setTVert msh j UV_array[j]
                if UV2_array.count > 0 do(
                        meshop.setNumMaps msh 3 keep:true
                        for i = 1 to UV2_array.count do (
                                meshop.setMapVert msh 2 i UV2_array[i]
                        )
                )
                if UV3_array.count > 0 do(
                        meshop.setNumMaps msh 4 keep:true
                        for i = 1 to UV3_array.count do (
                                meshop.setMapVert msh 3 i UV3_array[i]
                        )
                )
                if UV4_array.count > 0 do(
                        meshop.setNumMaps msh 5 keep:true
                        for i = 1 to UV4_array.count do (
                                meshop.setMapVert msh 4 i UV4_array[i]
                        )
                )
                if UV5_array.count > 0 do(
                        meshop.setNumMaps msh 6 keep:true
                        for i = 1 to UV5_array.count do (
                                meshop.setMapVert msh 5 i UV5_array[i]
                        )
                )
                for j = 1 to Face_array.count do (
                        setTVFace msh j Face_array[j]
                        setFaceMatID msh j MatID
                )
                if (use_vertex_colors == True):
                    for j = 1 to Color_array.count do setvertcolor msh j Color_array[j]
                    for j = 1 to Alpha_array.count do(meshop.setVertAlpha msh -2 j Alpha_array[j])

                for j = 1 to msh.numfaces do setFaceSmoothGroup msh j 1
                max modify mode
                select msh

                addmodifier msh (Edit_Normals ()) ui:off
                msh.Edit_Normals.MakeExplicit selection:#{1..Normal_array.count}
                EN_convertVS = msh.Edit_Normals.ConvertVertexSelection
                EN_setNormal = msh.Edit_Normals.SetNormal
                normID = #{}

                for v = 1 to Normal_array.count do(
                        free normID
                        EN_convertVS #{v} &normID
                        for id in normID do EN_setNormal id Normal_array[v]
                )

                if BoneCount > 0 do(
                    skinMod = skin ()
                    boneIDMap = []
                    addModifier msh skinMod
                    msh.Skin.weightAllVertices = false
                    for i = 1 to BoneCount do
                    (
                             maxbone = getnodebyname BoneArray[i].name
                             if i != BoneCount then
                                    skinOps.addBone skinMod maxbone 0
                             else
                                    skinOps.addBone skinMod maxbone 1
                    )

                    local numSkinBones = skinOps.GetNumberBones skinMod
                    for i = 1 to numSkinBones do
                    (
                            local boneName = skinOps.GetBoneName skinMod i 0
                            for j = 1 to BoneCount do
                            (
                                    if boneName == BoneArray[j].Name then
                                    (
                                            boneIDMap[j] = i
                                            j = BoneCount + 1
                                    )
                            )
                    ) # This fixes bone ordering in 3DS Max 2012. Thanks to sunnydavis for the fix!

                    modPanel.setCurrentObject skinMod

                    # These fix broken rigging for 3DS Max 2015 and above.
                    for i = 1 to Vert_array.count do(
                            skinOps.SetVertexWeights skinMod i 1 1
                            skinOps.unnormalizeVertex skinMod i true 
                            skinOps.SetVertexWeights skinMod i 1 0
                            skinOps.unnormalizeVertex skinMod i false
                    )
                    skinOps.RemoveZeroWeights skinMod

                    for i = 1 to Weight_array.count do (
                            w = Weight_array[i]
                            bi = [] # bone index array
                            wv = [] # weight value array

                            for j = 1 to w.boneids.count do
                            (
                                    boneid = w.boneids[j]
                                    weight = w.weights[j]
                                    append bi boneIDMap[boneid]
                                    append wv weight
                            )
                            skinOps.ReplaceVertexWeights skinMod i bi wv

        print("Done! ("+((((time.time())-time_start)*0.001))+" Seconds)")

# ==== Import OPERATOR ====
from bpy_extras.io_utils import (ImportHelper)

class NUMDLB_Import_Operator(bpy.types.Operator, ImportHelper):
    bl_idname = ("screen.numdlb_import")
    bl_label = ("NUMDLB Import")
    filename_ext = ".numdlb"
    filter_glob = bpy.props.StringProperty(default="*.numdlb", options={'HIDDEN'})
    
    use_vertex_colors = BoolProperty(
            name="Vertex Colors",
            description="Import vertex color information to meshes",
            default=True,
            )

    print_debug_info = BoolProperty(
            name="Debugging Information",
            description="Print extra information to console",
            default=False,
            )
    
    texture_ext = bpy.props.StringProperty(
            name="Texture File Extension",
            description="The file type to be associated with the texture names",
            default=".png",
            )

    def draw(self, context):
        layout = self.layout
        
        row = layout.row(align=True)
        row.prop(self, "use_vertex_colors")
        row.prop(self, "print_debug_info")
        row.prop(self, "texture_ext")
        
    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob",))
        getModelInfo(context, **keywords)

        if os.path.isfile(MATName):
            importMaterials(context, **keywords)
        if os.path.isfile(SKTName):
            importSkeleton(context, **keywords)
        if os.path.isfile(MSHName):
            importMeshes(context, **keywords)

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
