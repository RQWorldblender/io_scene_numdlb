import bitio, enum, io, math, mathutils, os, struct, sys, time

class AnimTrack:
    def __init__(self):
        self.name = ""
        self.type = ""
        self.flags = 0
        self.frameCount = 0
        self.dataOffset = 0
        self.dataSize = 0
        self.animations = []

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

    def __repr__(self):
        return "Flags: " + str(self.flags) + "\t| Bits/entry: " + str(self.bitsPerEntry) + "\t| Data offset: " + str(self.compressedDataOffset) + "\t| Frame count: " + str(self.frameCount) + "\n"

class AnimCompressedItem:
    def __init__(self):
        self.start = 0
        self.end = 0
        self.count = 0

    def __init__(self, start, end, count):
        self.start = start
        self.end = end
        self.count = count

    def __repr__(self):
        return "Start: " + str(self.start) + "\t| End: " + str(self.end) + "\t| Count: " + str(self.count) + "\n"

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
    ConstTransform = 512
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

# A standard linear interpolation function for individual values
def lerp(av, bv, v0, v1, factor):
    if (v0 == v1):
        return av
    if (factor == v0):
        return av
    if (factor == v1):
        return bv

    mu = (factor - v0) / (v1 - v0)
    return (av * (1 - mu)) + (bv * mu)

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
                BufferOffset = am.tell() + struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                BufferSize = struct.unpack('<L', am.read(4))[0]; am.seek(0x04, 1)
                print("GroupOffset: " + str(GroupOffset) + " | " + "GroupCount: " + str(GroupCount) + " | " + "BufferOffset: " + str(BufferOffset) + " | " + "BufferSize: " + str(BufferSize))
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
                        #print("NodeNameOffset: " + str(NodeNameOffset) + " | " + "NodeDataOffset: " + str(NodeDataOffset) + " | " + "NextNodePos: " + str(NextNodePos))
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
                am.seek(BufferOffset, 0) # This must happen or all data will be read incorrectly
                readAnimations(io.BytesIO(am.read(BufferSize)))
            else:
                raise RuntimeError("%s is not a valid NUANMB file." % filepath)

def readAnimations(ao):
    for ag in AnimGroups.items():
        for track in ag[1]:
            ao.seek(track.dataOffset, 0)    
            # Collect the actual data pertaining to every node
            if ((track.flags & 0xff00) == AnimTrackFlags.Constant.value or (track.flags & 0xff00) == AnimTrackFlags.ConstTransform.value):
                readDirectData(ao, track)
            if ((track.flags & 0xff00) == AnimTrackFlags.Direct.value):
                for t in range(track.frameCount):
                    readDirect(ao, track)
            if ((track.flags & 0xff00) == AnimTrackFlags.Compressed.value):
                readCompressedData(ao, track)
            print(track.name + " | " + AnimType(ag[0]).name)
            print(track.animations)

    ao.close()

def readDirectData(aq, track):
    if ((track.flags & 0x00ff) == AnimTrackFlags.Transform.value):
        # Scale [X, Y, Z]
        sx = struct.unpack('<f', aq.read(4))[0]; sy = struct.unpack('<f', aq.read(4))[0]; sz = struct.unpack('<f', aq.read(4))[0]
        # Rotaton [X, Y, Z, W]
        rx = struct.unpack('<f', aq.read(4))[0]; ry = struct.unpack('<f', aq.read(4))[0]; rz = struct.unpack('<f', aq.read(4))[0]; rw = struct.unpack('<f', aq.read(4))[0]
        # Position [X, Y, Z]
        px = struct.unpack('<f', aq.read(4))[0]; py = struct.unpack('<f', aq.read(4))[0]; pz = struct.unpack('<f', aq.read(4))[0]
        track.animations.append(mathutils.Matrix([[px, py, pz, 0], [rx, ry, rz, rw], [sx, sy, sz, 1]]))
        """
        Matrix composition:
                | X | Y | Z | W |
        Position|PX |PY |PZ |PW | 0
        Rotation|RX |RY |RZ |RW | 1
        Scale   |SX |SY |SZ |SW | 2
                  0   1   2   3
        PW and SW are not used here, instead being populated with '0' and '1', respectively
        """

    if ((track.flags & 0x00ff) == AnimTrackFlags.Texture.value):
        pass

    if ((track.flags & 0x00ff) == AnimTrackFlags.Float.value):
        track.animations.append(struct.unpack('<f', aq.read(4))[0])

    if ((track.flags & 0x00ff) == AnimTrackFlags.PatternIndex.value):
        pass

    if ((track.flags & 0x00ff) == AnimTrackFlags.Boolean):
        track.animations.append(struct.unpack('<B', aq.read(1))[0] == 1)

    if ((track.flags & 0x00ff) == AnimTrackFlags.Vector4):
        # [X, Y, Z, W]
        x = struct.unpack('<f', aq.read(4))[0]; y = struct.unpack('<f', aq.read(4))[0]; z = struct.unpack('<f', aq.read(4))[0]; w = struct.unpack('<f', aq.read(4))[0]
        track.animations.append(mathutils.Vector([x, y, z, w]))

def readCompressedData(aq, track):
    ach = AnimCompressedHeader()
    ach.unk_4 = struct.unpack('<H', aq.read(2))[0]
    ach.flags = struct.unpack('<H', aq.read(2))[0]
    ach.defaultDataOffset = struct.unpack('<H', aq.read(2))[0]
    ach.bitsPerEntry = struct.unpack('<H', aq.read(2))[0]
    ach.compressedDataOffset = struct.unpack('<L', aq.read(4))[0]
    ach.frameCount = struct.unpack('<L', aq.read(4))[0]
    print(ach)
    if ((track.flags & 0x00ff) == AnimTrackFlags.Transform.value):
        acj = [] # Contains an array of AnimCompressedItem objects
        for i in range(9):
            Start = struct.unpack('<f', aq.read(4))[0]
            End = struct.unpack('<f', aq.read(4))[0]
            Count = struct.unpack('<L', aq.read(4))[0]; aq.seek(0x04, 1)
            aci = AnimCompressedItem(Start, End, Count)
            acj.append(aci)
        #print(acj)

        aq.seek(track.dataOffset + ach.defaultDataOffset, 0)
        # Scale [X, Y, Z]
        sx = struct.unpack('<f', aq.read(4))[0]; sy = struct.unpack('<f', aq.read(4))[0]; sz = struct.unpack('<f', aq.read(4))[0]
        # Rotaton [X, Y, Z, W]
        rx = struct.unpack('<f', aq.read(4))[0]; ry = struct.unpack('<f', aq.read(4))[0]; rz = struct.unpack('<f', aq.read(4))[0]; rw = struct.unpack('<f', aq.read(4))[0]
        # Position [X, Y, Z, W]
        px = struct.unpack('<f', aq.read(4))[0]; py = struct.unpack('<f', aq.read(4))[0]; pz = struct.unpack('<f', aq.read(4))[0]; pw = struct.unpack('<H', aq.read(2))[0]

        aq.seek(track.dataOffset + ach.compressedDataOffset, 0)
        for f in range(ach.frameCount):
            transform = mathutils.Matrix([[px, py, pz, pw], [rx, ry, rz, rw], [sx, sy, sz, 1]])
            """
            Matrix composition:
                    | X | Y | Z | W |
            Position|PX |PY |PZ |PW | 0
            Rotation|RX |RY |RZ |RW | 1
            Scale   |SX |SY |SZ |SW | 2
                      0   1   2   3
            SW is used to represent absolute scale, being populated with '1' by default
            """

            for itemIndex in range(len(acj)):
                # First check if this track should be parsed
                # TODO: Don't hard code these flags.
                if (not ((itemIndex == 0 and (ach.flags & 0x3) == 0x3) # isotropic scale
                    or (itemIndex >= 0 and itemIndex <= 2 and (ach.flags & 0x3) == 0x1) # normal scale
                    or (itemIndex > 2 and itemIndex <= 5 and (ach.flags & 0x4) > 0)
                    or (itemIndex > 5 and itemIndex <= 8 and (ach.flags & 0x8) > 0))):
                    continue

                item = acj[itemIndex]
                # Decompress
                valueBitCount = item.count
                if (valueBitCount == 0):
                    continue

                br = bitio.BitReader(aq)
                value = br.readbits(valueBitCount)
                scale = 0
                for k in range(valueBitCount):
                    scale = scale | (0x1 << k)

                frameValue = lerp(item.start, item.end, 0, 1, value / float(scale))
                if frameValue == float('NaN'):
                    frameValue = 0

                # The 'Transform' type frequently depends on flags
                if ((ach.flags & 0x3) == 0x3):
                    # Scale isotropic
                    if (itemIndex == 0):
                        transform[2][3] = frameValue

                if ((ach.flags & 0x3) == 0x1):
                    # Scale normal
                    if (itemIndex == 0):
                        transform[2][0] = frameValue
                    elif (itemIndex == 1):
                        transform[2][1] = frameValue
                    elif (itemIndex == 2):
                        transform[2][2] = frameValue

                # Rotation and Position
                if (itemIndex == 3):
                    transform[1][0] = frameValue
                elif (itemIndex == 4):
                    transform[1][1] = frameValue
                elif (itemIndex == 5):
                    transform[1][2] = frameValue
                elif (itemIndex == 6):
                    transform[0][0] = frameValue
                elif (itemIndex == 7):
                    transform[0][1] = frameValue
                elif (itemIndex == 8):
                    transform[0][2] = frameValue

            # Rotations have an extra bit at the end
            if ((ach.flags & 0x4) > 0):
                br = bitio.BitReader(aq)
                wFlip = br.readbits(1) == 1

                # W is calculated
                transform[1][3] = math.sqrt(abs(1 - (pow(transform[1][0], 2) + pow(transform[1][1], 2) + pow(transform[1][2], 2))))

                if wFlip:
                    transform[1][3] *= -1

            track.animations.append(transform)

    if ((track.flags & 0x00ff) == AnimTrackFlags.Texture.value):
        print("Compressed texture data extraction not yet implemented")

    if ((track.flags & 0x00ff) == AnimTrackFlags.Float.value):
        print("Compressed float data extraction not yet implemented")

    if ((track.flags & 0x00ff) == AnimTrackFlags.PatternIndex.value):
        print("Compressed pattern index data extraction not yet implemented")

    if ((track.flags & 0x00ff) == AnimTrackFlags.Boolean):
        aq.seek(track.dataOffset + ach.compressedDataOffset, 0)
        for t in range(ach.frameCount):
            track.animations.append(readBits(aq, ach.bitsPerEntry) == 1)

    if ((track.flags & 0x00ff) == AnimTrackFlags.Vector4):
        acj = [] # Contains an array of AnimCompressedItem objects
        for i in range(4):
            Start = struct.unpack('<f', aq.read(4))[0]
            End = struct.unpack('<f', aq.read(4))[0]
            Count = struct.unpack('<L', aq.read(4))[0]; aq.seek(0x04, 1)
            aci = AnimCompressedItem(Start, End, Count)
            acj.append(aci)
        #print(acj)

        values = []
        # Copy default values
        for c in range(4):
            values.append(struct.unpack('<f', aq.read(4))[0])

        aq.seek(track.dataOffset + ach.compressedDataOffset, 0)
        for f in range(ach.frameCount):
            for itemIndex in range(len(acj)):
                item = acj[itemIndex]
                # Decompress
                valueBitCount = item.count
                if (valueBitCount == 0):
                    continue

                br = bitio.BitReader(aq)
                value = br.readbits(valueBitCount)
                scale = 0
                for k in range(valueBitCount):
                    scale = scale | (0x1 << k)

                frameValue = lerp(item.start, item.end, 0, 1, value / float(scale))
                if frameValue == float('NaN'):
                    frameValue = 0

                values[itemIndex] = frameValue

            track.animations.append(values)

#animpath = "/home/richard/Desktop/update-2.0.0/fighter/packun/motion/body/c00/a00wait1.nuanmb"
animpath = "/home/richard/Desktop/update-2.0.0/fighter/packun/motion/body/c00/a01turn.nuanmb"

getAnimationInfo(animpath)
