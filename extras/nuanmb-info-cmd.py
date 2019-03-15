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
                print("MODLNameOff: " + str(MODLNameOff))
                SKTNameOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                print("SKTNameOff: " + str(SKTNameOff))
                MATNameOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                print("MATNameOff: " + str(MATNameOff))
                md.seek(0x10, 1)
                MSHNameOff = md.tell() + struct.unpack('<L', md.read(4))[0]; md.seek(0x04, 1)
                print("MSHNameOff: " + str(MSHNameOff))
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

def importAnimations(animpath):
    global animName; animName = ""
    global BoneCount; BoneCount = 0
    global BoneArray; BoneArray = []
    global animations_Array; animations_Array = []
    global BoneTrsArray; BoneTrsArray = []
    global BoneParent_array; BoneParent_array = []
    global BoneName_array; BoneName_array = []
    global skelName; skelName = ""
    
    if os.path.isfile(animpath):
        with open(animpath, 'rb') as am:
            am.seek(0x10, 0)
            AnimCheck = struct.unpack('<L', am.read(4))[0]
            if (AnimCheck == 0x414E494D):
                #am.seek(0x1C, 0)
                AnimVerA = struct.unpack('<H', am.read(2))[0]
                AnimVerB = struct.unpack('<H', am.read(2))[0]
                print(str(AnimVerA) + " | " + str(AnimVerB))
                am.seek(0x48, 0)
                #SomeOff = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                print(str(am.tell()))
                #AnimNameOff = am.tell() + struct.unpack('<L', am.read(4))[0]
                #print("AnimNameOff: " + str(AnimNameOff))
                #am.seek(AnimNameOff, 0)
                AnimName = readVarLenString(am); am.seek(0x04, 1)
                print("animName: " + AnimName)
                """
                BoneMatrOffset = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                BoneMatrCount = struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                BoneInvMatrOffset = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                BoneInvMatrCount = struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                BoneRelMatrOffset = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                BoneRelMatrCount = struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                BoneRelMatrInvOffset = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                BoneRelMatrInvCount = struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                Unk1 = 0
                Unk2 = 0
                am.seek(BoneOffset, 0)

                for c in range(BoneCount):
                    BoneNameOffset = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                    BoneRet = am.tell()
                    am.seek(BoneNameOffset, 0)
                    BoneName = readVarLenString(b)
                    am.seek(BoneRet, 0)
                    BoneID = struct.unpack('<H', am.read(2))[0]
                    BoneParent = struct.unpack('<H', am.read(2))[0]
                    BoneUnk = struct.unpack('<L', am.read(4))[0]
                    BoneParent_array.append(BoneParent)
                    BoneName_array.append(BoneName)

                print("Total number of bones found: " + str(BoneCount))
                print(BoneParent_array)
                print(BoneName_array)
                """
            else:
                raise RuntimeError("%s is not a valid NUANMB file." % filepath)


animpath = "/opt/Smash Ultimate Models/fighter/packun/motion/body/c00/a00wait1.nuanmb"
#modelpath = "/opt/Smash Ultimate Models/fighter/kirby/model/body/c00/model.numdlb"

#getModelInfo(modelpath)
importAnimations(animpath)
