import io, os, struct, sys, time

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
"""
class MODLStruct:
    # struct MODLStruct (MSHGrpName, MSHMatName)
    def __init__(self):
        self.meshGroupName = ""
        self.meshMaterialName = ""

    def __init__(self, meshGroupName, meshMaterialName):
        self.meshGroupName = meshGroupName
        self.meshMaterialName = meshMaterialName

    def __repr__(self):
        return "Mesh group name: " + str(self.meshGroupName) + "\t| Mesh material name: " + str(self.meshMaterialName) + "\n"
"""
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

# Global variables used by all of the main functions
dirPath = ""
MODLName = ""
SKTName = ""
MATName = ""
MSHName = ""
MODLGrp_array = {}
Materials_array = []
BoneCount = 0
BoneArray = ["Trans", "Rot"]
BoneFixArray = []
BoneTrsArray = []
BoneParent_array = []
BoneName_array = []
PolyGrp_array = []
WeightGrp_array = []
print_debug_info = True
texture_ext = ".png"

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

def getModelInfo(filepath):
    if os.path.isfile(filepath):
        with open(filepath, 'rb') as md:
            global dirPath
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
                global MODLName
                MODLName = readVarLenString(md)
                md.seek(SKTNameOff, 0)
                global SKTName
                SKTName = os.path.join(dirPath, readVarLenString(md))
                print(SKTName)
                md.seek(MATNameOff, 0)
                MATNameStrLen = struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                global MATName
                MATName = os.path.join(dirPath, readVarLenString(md))
                print(MATName)
                md.seek(MSHNameOff, 0)
                global MSHName
                MSHName = os.path.join(dirPath, readVarLenString(md)); md.seek(0x04, 1)
                print(MSHName)
                md.seek(MSHDatOff, 0)
                global MODLGrp_array
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
                if print_debug_info:
                    print(MODLGrp_array)

# Imports the materials
def importMaterials(MATName):
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

            #for m in range(MATCount):
            #    print(os.path.join(os.path.relpath(dirPath), Materials_array[m].color1Name + texture_ext))
            #    print(Materials_array[m].color2Name == "")
            #    print(os.path.join(os.path.relpath(dirPath), Materials_array[m].color2Name + texture_ext))
        if print_debug_info:
            print(Materials_array)

# Imports the skeleton
def importSkeleton(SKTName):
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
            if print_debug_info:
                print(BoneParent_array)
                print(BoneName_array)

            b.seek(BoneMatrOffset, 0)
            for c in range(BoneCount):
                # Matrix format is [X, Y, Z, W]
                m11 = struct.unpack('<f', b.read(4))[0]; m12 = struct.unpack('<f', b.read(4))[0]; m13 = struct.unpack('<f', b.read(4))[0]; m14 = struct.unpack('<f', b.read(4))[0]
                m21 = struct.unpack('<f', b.read(4))[0]; m22 = struct.unpack('<f', b.read(4))[0]; m23 = struct.unpack('<f', b.read(4))[0]; m24 = struct.unpack('<f', b.read(4))[0]
                m31 = struct.unpack('<f', b.read(4))[0]; m32 = struct.unpack('<f', b.read(4))[0]; m33 = struct.unpack('<f', b.read(4))[0]; m34 = struct.unpack('<f', b.read(4))[0]
                m41 = struct.unpack('<f', b.read(4))[0]; m42 = struct.unpack('<f', b.read(4))[0]; m43 = struct.unpack('<f', b.read(4))[0]; m44 = struct.unpack('<f', b.read(4))[0]
                tfm = [m11, m21, m31, m41, m12, m22, m32, m42, m13, m23, m33, m43, m14, m24, m34, m44]
                if print_debug_info:
                    print(tfm)
                    print("Matrix for " + BoneName_array[c] + ":\n" + str(tfm))

                BoneArray.append(BoneName_array[c])
                BoneTrsArray.append(tfm)

# Imports the meshes
def importMeshes(MSHName):
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
            global PolyGrp_array
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
                if print_debug_info:
                    print(ge.visGroupName + " unknowns: 1: " + str(Unk1) + "\t| Off1: " + str(UnkOff1) + "\t| 2: " + str(Unk2) + "\t| 3: " + str(Unk3) + "\t| 4: " + str(Unk4) + "\t| 5: " + str(Unk5) + "\t| 6: " + str(Unk6) + "\t| LongFace: " + str(ge.faceLongBit) + "\t| 8: " + str(Unk8) + "\t| Sort: " + str(SortPriority) + "\t| 9: " + str(Unk9) + "\t| 10: " + str(Unk10))
                f.seek(PolyGrpRet, 0)

            if print_debug_info:
                print(PolyGrp_array)

            f.seek(VertBuffOffset, 0)
            VertOffStart = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            VertBuffSize = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            UVOffStart = f.tell() + struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)
            UVBuffSize = struct.unpack('<L', f.read(4))[0]; f.seek(0x04, 1)

            f.seek(WeightBuffOffset, 0)
            global WeightGrp_array
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

            if print_debug_info:
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

                if print_debug_info:
                    print(PolyGrp_array[p].visGroupName + " Vert start: " + str(f.tell()))
                for v in range(PolyGrp_array[p].verticeCount):
                    if (PosFmt == 1):
                        vx = struct.unpack('<f', f.read(4))[0]
                        vy = struct.unpack('<f', f.read(4))[0]
                        vz = struct.unpack('<f', f.read(4))[0]
                        Vert_array.append([vx,vy,vz])
                    else:
                        print("Unknown position format!")
                    if (NormFmt == 6):
                        nx = decompressHalfFloat(f.read(2)) * 2 
                        ny = decompressHalfFloat(f.read(2)) * 2
                        nz = decompressHalfFloat(f.read(2)) * 2
                        nq = decompressHalfFloat(f.read(2)) * 2
                        Normal_array.append([nx,ny,nz])
                    else:
                        print("Unknown normals format!")
                    if (TanFmt == 6):
                        tanx = decompressHalfFloat(f.read(2)) * 2
                        tany = decompressHalfFloat(f.read(2)) * 2
                        tanz = decompressHalfFloat(f.read(2)) * 2
                        tanq = decompressHalfFloat(f.read(2)) * 2
                    else:
                        print("Unknown tangents format!")

                if print_debug_info:
                    print(PolyGrp_array[p].visGroupName + " Vert end: " + str(f.tell()))
                    #print(Vert_array)
                # Read UV map data
                f.seek(UVOffStart + PolyGrp_array[p].UVStart, 0)

                if print_debug_info:
                    print(PolyGrp_array[p].visGroupName + " UV start: " + str(f.tell()))
                for v in range(PolyGrp_array[p].verticeCount):
                    if (UVCount == 0):
                        UV_array.append([0,0,0])
                    elif (UVCount == 1):
                        tu = (decompressHalfFloat(f.read(2)) * 2)
                        tv = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                        UV_array.append([tu,tv,0])
                    elif (UVCount == 2):
                        tu = (decompressHalfFloat(f.read(2)) * 2)
                        tv = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                        tu2 = (decompressHalfFloat(f.read(2)) * 2)
                        tv2 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                        UV_array.append([tu,tv,0])
                        UV2_array.append([tu2,tv2,0])
                    elif (UVCount == 3):
                        tu = (decompressHalfFloat(f.read(2)) * 2)
                        tv = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                        tu2 = (decompressHalfFloat(f.read(2)) * 2)
                        tv2 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                        tu3 = (decompressHalfFloat(f.read(2)) * 2)
                        tv3 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                        UV_array.append([tu,tv,0])
                        UV2_array.append([tu2,tv2,0])
                        UV3_array.append([tu3,tv3,0])
                    elif (UVCount == 4):
                        tu = (decompressHalfFloat(f.read(2)) * 2)
                        tv = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                        tu2 = (decompressHalfFloat(f.read(2)) * 2)
                        tv2 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                        tu3 = (decompressHalfFloat(f.read(2)) * 2)
                        tv3 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                        tu4 = (decompressHalfFloat(f.read(2)) * 2)
                        tv4 = ((decompressHalfFloat(f.read(2)) * 2) * -1) + 1
                        UV_array.append([tu,tv,0])
                        UV2_array.append([tu2,tv2,0])
                        UV3_array.append([tu3,tv3,0])
                        UV4_array.append([tu4,tv4,0])
                    elif (UVCount == 5):
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
                        UV_array.append([tu,tv,0])
                        UV2_array.append([tu2,tv2,0])
                        UV3_array.append([tu3,tv3,0])
                        UV4_array.append([tu4,tv4,0])
                        UV5_array.append([tu5,tv5,0])
                    else:
                        print("Importing more than 5 UV sets is not supported, skipping this set.")
                    # Read vertex color data
                    if (ColorCount == 0):
                        Color_array.append([128,128,128])
                        Alpha_array.append(1)
                    elif (ColorCount == 1):
                        colorr = struct.unpack('<B', f.read(1))[0] #unsigned
                        colorg = struct.unpack('<B', f.read(1))[0] #unsigned
                        colorb = struct.unpack('<B', f.read(1))[0] #unsigned
                        colora = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                        Color_array.append([colorr,colorg,colorb]); Alpha_array.append(colora)
                    elif (ColorCount == 2):
                        colorr = struct.unpack('<B', f.read(1))[0] #unsigned
                        colorg = struct.unpack('<B', f.read(1))[0] #unsigned
                        colorb = struct.unpack('<B', f.read(1))[0] #unsigned
                        colora = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                        colorr2 = struct.unpack('<B', f.read(1))[0] #unsigned
                        colorg2 = struct.unpack('<B', f.read(1))[0] #unsigned
                        colorb2 = struct.unpack('<B', f.read(1))[0] #unsigned
                        colora2 = float(struct.unpack('<B', f.read(1))[0]) / 128 #unsigned as float) / 128
                        Color_array.append([colorr,colorg,colorb]); Alpha_array.append(colora)
                        Color2_array.append([colorr2,colorg2,colorb2]); Alpha2_array.append(colora2)
                    elif (ColorCount == 3):
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
                        Color_array.append([colorr,colorg,colorb]); Alpha_array.append(colora)
                        Color2_array.append([colorr2,colorg2,colorb2]); Alpha2_array.append(colora2)
                        Color3_array.append([colorr3,colorg3,colorb3]); Alpha3_array.append(colora3)
                    elif (ColorCount == 4):
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
                        Color_array.append([colorr,colorg,colorb]); Alpha_array.append(colora)
                        Color2_array.append([colorr2,colorg2,colorb2]); Alpha2_array.append(colora2)
                        Color3_array.append([colorr3,colorg3,colorb3]); Alpha3_array.append(colora3)
                        Color4_array.append([colorr4,colorg4,colorb4]); Alpha4_array.append(colora4)
                    elif (ColorCount == 5):
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
                        Color_array.append([colorr,colorg,colorb]); Alpha_array.append(colora)
                        Color2_array.append([colorr2,colorg2,colorb2]); Alpha2_array.append(colora2)
                        Color3_array.append([colorr3,colorg3,colorb3]); Alpha3_array.append(colora3)
                        Color4_array.append([colorr4,colorg4,colorb4]); Alpha4_array.append(colora4)
                        Color5_array.append([colorr5,colorg5,colorb5]); Alpha5_array.append(colora5)
                    else:
                        print("Importing more than 5 vertex color sets is not supported, skipping this set.")

                if print_debug_info:
                    print(PolyGrp_array[p].visGroupName + " UV end: " + str(f.tell()))
                # Read face data
                f.seek(FaceBuffOffset + PolyGrp_array[p].facepointStart, 0)
                if print_debug_info:
                    print(PolyGrp_array[p].visGroupName + " Face start: " + str(f.tell()))
                for fc in range(int(PolyGrp_array[p].facepointCount / 3)):
                    if (PolyGrp_array[p].faceLongBit == 0):
                        fa = struct.unpack('<H', f.read(2))[0] + 1 #unsigned + 1
                        fb = struct.unpack('<H', f.read(2))[0] + 1 #unsigned + 1
                        fc = struct.unpack('<H', f.read(2))[0] + 1 #unsigned + 1
                        Face_array.append([fa,fb,fc])

                    elif (PolyGrp_array[p].faceLongBit == 1):
                        fa = struct.unpack('<L', f.read(4))[0] + 1 #unsigned + 1
                        fb = struct.unpack('<L', f.read(4))[0] + 1 #unsigned + 1
                        fc = struct.unpack('<L', f.read(4))[0] + 1 #unsigned + 1
                        Face_array.append([fa,fb,fc])
                    else:
                        raise RuntimeError("Unknown face bit value!")

                if print_debug_info:
                    print(PolyGrp_array[p].visGroupName + " Face end: " + str(f.tell()))
                    #print(Face_array)

                if (PolyGrp_array[p].singleBindName != ""):
                    for b in range(len(BoneArray)):
                       if (PolyGrp_array[p].singleBindName == BoneArray[b]):
                           SingleBindID = b

                    for b in range(len(Vert_array)):
                        Weight_array.append(weight_data([SingleBindID], [1.0]))
                else:
                    for b in range(len(Vert_array)):
                        Weight_array.append(weight_data([0], [0]))

                    RigSet = 1
                    for b in range(len(WeightGrp_array)):
                            if (PolyGrp_array[p].visGroupName == WeightGrp_array[b].groupName):
                                RigSet = b
                                # WeightGrp_array[b].groupName = "" # Dumb fix due to shared group names but split entries, prevents crashing.
                                break
                    # Read vertice/weight group data
                    f.seek(WeightGrp_array[RigSet].rigInfOffset, 0)
                    if print_debug_info:
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
                            for b in range(len(BoneArray)):
                                if (RigBoneName == BoneArray[b]):
                                    RigBoneID = b

                            if (RigBoneID == 0):
                                print(RigBoneName + " doesn't exist on " + PolyGrp_array[p].visGroupName + "! Transferring rigging to " + BoneArray[1] + ".")
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
                            Weight_array.append(weight_data([1], [1.0]))

                    print(Weight_array)

                #print(findUVImageForMesh(MODLGrp_array[PolyGrp_array[p].visGroupName], False) + texture_ext)
                #print(findUVImageForMesh(MODLGrp_array[PolyGrp_array[p].visGroupName], True) + texture_ext)

        print("Done! Mesh import completed in " + str((time.time()-time_start)) + " seconds.")

#modelpath = "/home/richard/Desktop/update-2.0.0/fighter/packun/model/body/c00/model.numdlb"
modelpath = "/media/richard/3AEE25744CE0956E/Smash Ultimate Models/fighter/mario/model/body/c00/model.numdlb"
getModelInfo(modelpath)

#importMaterials(MATName)
importSkeleton(SKTName)
importMeshes(MSHName)
