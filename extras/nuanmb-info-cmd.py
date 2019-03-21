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

# Global variables used by all of the main functions
AnimName = ""
FrameCount = 0
BoneCount = 0
Animations_array = []
BoneTrsArray = []

def readVarLenString(file):
    nameBuffer = []
    while('\x00' not in nameBuffer):
        nameBuffer.append(str(file.read(1).decode("utf-8", "ignore")))
    del nameBuffer[-1]
    return ''.join(nameBuffer)

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
                AnimVerA = struct.unpack('<H', am.read(2))[0]
                AnimVerB = struct.unpack('<H', am.read(2))[0]
                #print(str(AnimVerA) + " | " + str(AnimVerB))
                FrameCount = struct.unpack('<f', am.read(4))[0]
                print(FrameCount)
                Unk1 = struct.unpack('<H', am.read(2))[0]
                Unk2 = struct.unpack('<H', am.read(2))[0]
                #print(str(Unk1) + " | " + str(Unk2))
                AnimNameOff = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                SomeVar1 = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                SomeVar2 = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                SomeVar3 = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                SomeVar4 = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                print("1: " + str(SomeVar1) + " | " + "2: " + str(SomeVar2) + " | " + "3: " + str(SomeVar3) + " | "+ "4: " + str(SomeVar4))
                am.seek(AnimNameOff, 0)
                AnimName = readVarLenString(am); am.seek(0x04, 1)
                print("AnimName: " + AnimName)
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


animpath = "/home/richard/Desktop/update-2.0.0/fighter/packun/motion/body/c00/a01turn.nuanmb"

importAnimations(animpath)
