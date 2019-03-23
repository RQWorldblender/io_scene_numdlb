import enum, io, os, struct, sys, time

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

class AnimTrack:
    def __init__(self):
        self.name = ""
        self.type = ""
        self.flags = 0
        self.frameCount = 0
        self.dataOffset = 0
        self.dataSize = 0
        self.transformAnim = []
        self.visibilityAnim = []
        self.materialAnim = []
        self.cameraAnim = []

    def __repr__(self):
        return "Node name: " + str(self.name) + "\t| Type: " + str(self.type) + "\t| Flags: " + str(self.flags) + "\t| # of frames: " + str(self.frameCount) + "\t| Data offset: " + str(self.dataOffset) + "\t| Data size: " + str(self.dataSize) + "\n"

class AnimCompressedHeader:
    def __init__(self):
        self.unk_4 = 0 # always 4?
        self.flags = 0
        self.defaultDataOffset = 0
        self.bitsPerEntry = 0
        self.compressedDataOffset = 0
        self.frameCount = 0

    def __init__(self, unk_4, flags, defaultDataOffset, bitsPerEntry, compressedDataOffset, frameCount):
        self.unk_4 = unk_4 # always 4?
        self.flags = flags
        self.defaultDataOffset = defaultDataOffset
        self.bitsPerEntry = bitsPerEntry
        self.compressedDataOffset = compressedDataOffset
        self.frameCount = frameCount

class AnimCompressedItem:
    def __init__(self):
        self.start = 0
        self.end = 0
        self.count = 0

    def __init__(self, start, end, count):
        self.start = start
        self.end = end
        self.count = count

class AnimType(enum.Enum):
    Transform = 1
    Visibility = 2
    Material = 4
    Camera = 5

class AnimTrackFlags(enum.Enum):
    Transform = 1
    Texture = 2
    Float = 3
    PatternIndex = 5
    Boolean = 8
    Vector4 = 9
    Direct = 256
    ConstTramsform = 512
    Compressed = 1024
    Constant = 1280
    # Use 65280 or 0xff00 when performing a bitwise 'and' on a flag
    # Use 255 or 0x00ff when performing a bitwise 'and' on a flag, for uncompressed data

def readVarLenString(file):
    nameBuffer = []
    while('\x00' not in nameBuffer):
        nameBuffer.append(str(file.read(1).decode("utf-8", "ignore")))
    del nameBuffer[-1]
    return ''.join(nameBuffer)

def getAnimationInfo(animpath):
    global AnimName; AnimName = ""
    GroupCount = 0
    global FrameCount; FrameCount = 0
    NodeCount = 0
    global AnimGroups; AnimGroups = {}
    # Structure of this dict is: {AnimType (numeric): an array of AnimTrack objects}
    
    if os.path.isfile(animpath):
        with open(animpath, 'rb') as am:
            am.seek(0x10, 0)
            AnimCheck = struct.unpack('<L', am.read(4))[0]
            if (AnimCheck == 0x414E494D):
                AnimVerA = struct.unpack('<H', am.read(2))[0]
                AnimVerB = struct.unpack('<H', am.read(2))[0]
                #print(str(AnimVerA) + " | " + str(AnimVerB))
                FrameCount = struct.unpack('<f', am.read(4))[0]
                print("Total # of frames: " + str(FrameCount))
                Unk1 = struct.unpack('<H', am.read(2))[0]
                Unk2 = struct.unpack('<H', am.read(2))[0]
                #print(str(Unk1) + " | " + str(Unk2))
                AnimNameOffset = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                GroupOffset = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                GroupCount = struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                Buffer1 = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                Buffer2 = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                print("GroupOffset: " + str(GroupOffset) + " | " + "GroupCount: " + str(GroupCount) + " | " + "Buffer1: " + str(Buffer1) + " | " + "Buffer2: " + str(Buffer2))
                am.seek(AnimNameOffset, 0)
                AnimName = readVarLenString(am); am.seek(0x04, 1)
                print("AnimName: " + AnimName)
                am.seek(GroupOffset, 0)
                # Collect information about the nodes
                for g in range(GroupCount):
                    NodeAnimType = struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                    NodeOffset = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                    NodeCount = struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                    AnimGroups[NodeAnimType] = [] # Create empty array to append to later on
                    NextGroupPos = am.tell()
                    print("AnimType: " + AnimType(NodeAnimType).name + " | " + "NodeOffset: " + str(NodeOffset) + " | " + "NodeCount: " + str(NodeCount) + " | NextGroupPos: " + str(NextGroupPos))
                    am.seek(NodeOffset, 0)
                    for n in range(NodeCount):
                        NodeNameOffset = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                        NodeDataOffset = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                        NextNodePos = am.tell() + struct.unpack('<L', am.read(4))[0] + 0x07
                        print("NodeNameOffset: " + str(NodeNameOffset) + " | " + "NodeDataOffset: " + str(NodeDataOffset) + " | " + "NextNodePos: " + str(NextNodePos))
                        am.seek(NodeNameOffset, 0)
                        at = AnimTrack()
                        at.name = readVarLenString(am)
                        am.seek(NodeDataOffset + 0x08, 0)
                        at.flags = struct.unpack('<L', am.read(4))[0]
                        at.frameCount = struct.unpack('<L', am.read(4))[0]
                        Unk3_0 = struct.unpack('<L', am.read(4))[0]
                        at.dataOffset = struct.unpack('<L', am.read(4))[0]
                        at.dataSize = struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                        at.type = readVarLenString(am)
                        print("NodeName: " + str(at.name) + " | " + "TrackFlags: " + str(at.flags) + " | " + "TrackFrameCount: " + str(at.frameCount) + " | " + "Unk3: " + str(Unk3_0) + " | " + "TrackDataOffset: " + str(at.dataOffset) +" | " + "TrackDataSize: " + str(at.dataSize))
                        AnimGroups[NodeAnimType].append(at)
                        am.seek(NextNodePos, 0)
                    print("---------")
                    am.seek(NextGroupPos, 0)
                print(AnimGroups)
                readAnimations(am)
            else:
                raise RuntimeError("%s is not a valid NUANMB file." % filepath)

def readAnimations(ao):
    for ag in AnimGroups.items():
        for track in ag[1]:
            ao.seek(track.dataOffset, 0)    
            # Collect the actual data pertaining to every node
            if (ag[0] == AnimType.Material.value):
                if ((track.flags & 0xff00) == AnimTrackFlags.Constant.value or (track.flags & 0xff00) == AnimTrackFlags.ConstTramsform.value):
                    track.materialAnim.append(readDirectData(ao, track))
                if ((track.flags & 0xff00) == AnimTrackFlags.Direct.value):
                    for t in range(track.frameCount):
                        track.materialAnim.append(readDirect(ao, track))
                if ((track.flags & 0xff00) == AnimTrackFlags.Compressed.value):
                    readCompressedData(ao, track)
                print(track.name + " | " + AnimType.Material.name)
                #print(track.materialAnim)

            elif (ag[0] == AnimType.Visibility.value):
                if ((track.flags & 0xff00) == AnimTrackFlags.Constant.value or (track.flags & 0xff00) == AnimTrackFlags.ConstTramsform.value):
                    track.visibilityAnim.append(readDirectData(ao, track))
                if ((track.flags & 0xff00) == AnimTrackFlags.Direct.value):
                    for t in range(track.frameCount):
                        track.visibilityAnim.append(readDirect(ao, track))
                if ((track.flags & 0xff00) == AnimTrackFlags.Compressed.value):
                    readCompressedData(ao, track)
                print(track.name + " | " + AnimType.Visibility.name)
                #print(track.visibilityAnim)

            elif (ag[0] == AnimType.Transform.value):
                if ((track.flags & 0xff00) == AnimTrackFlags.Constant.value or (track.flags & 0xff00) == AnimTrackFlags.ConstTramsform.value):
                    track.transformAnim.append(readDirectData(ao, track))
                if ((track.flags & 0xff00) == AnimTrackFlags.Direct.value):
                    for t in range(track.frameCount):
                        track.transformAnim.append(readDirect(ao, track))
                if ((track.flags & 0xff00) == AnimTrackFlags.Compressed.value):
                    readCompressedData(ao, track)
                print(track.name + " | " + AnimType.Transform.name)
                #print(track.transformAnim)

            elif (ag[0] == AnimType.Camera.value):
                print("Camera data extraction not yet implemented")

def readDirectData(aq, track):
    if ((track.flags & 0x00ff) == AnimTrackFlags.Transform.value):
        # Scale [X, Y, Z]
        sx = struct.unpack('<f', aq.read(4))[0]; sy = struct.unpack('<f', aq.read(4))[0]; sz = struct.unpack('<f', aq.read(4))[0]
        # Rotaton [X, Y, Z, W]
        rx = struct.unpack('<f', aq.read(4))[0]; ry = struct.unpack('<f', aq.read(4))[0]; rz = struct.unpack('<f', aq.read(4))[0]; rw = struct.unpack('<f', aq.read(4))[0]
        # Position [X, Y, Z]
        px = struct.unpack('<f', aq.read(4))[0]; py = struct.unpack('<f', aq.read(4))[0]; pz = struct.unpack('<f', aq.read(4))[0]
        return [[px, py, pz], [rx, ry, rz, rw], [sx, sy, sz]]
    if ((track.flags & 0x00ff) == AnimTrackFlags.Texture.value):
        pass
    if ((track.flags & 0x00ff) == AnimTrackFlags.Float.value):
        return struct.unpack('<f', aq.read(4))[0]
    if ((track.flags & 0x00ff) == AnimTrackFlags.PatternIndex.value):
        pass
    if ((track.flags & 0x00ff) == AnimTrackFlags.Boolean):
        return struct.unpack('<B', aq.read(1))[0] == 1
    if ((track.flags & 0x00ff) == AnimTrackFlags.Vector4):
        # [X, Y, Z, W]
        x = struct.unpack('<f', aq.read(4))[0]; y = struct.unpack('<f', aq.read(4))[0]; z = struct.unpack('<f', aq.read(4))[0]; w = struct.unpack('<f', aq.read(4))[0]
        return [x, y, z, w]

def readCompressedData(aq, track):
    print("Compressed data extraction not yet implemented")

animpath = "/home/richard/Desktop/update-2.0.0/fighter/packun/motion/body/c00/a00wait1.nuanmb"
#animpath = "/home/richard/Desktop/update-2.0.0/fighter/packun/motion/body/c00/a01turn.nuanmb"

getAnimationInfo(animpath)
