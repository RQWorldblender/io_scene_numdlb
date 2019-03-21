#!BPY

"""
Name: 'Super Smash Bros. Ultimate Animation Importer (.nuanmb)...'
Blender: 270
Group: 'Import'
Tooltip: 'Import *.NUANMB (.nuanmb)'
"""

__author__ = ["Richard Qian (Worldblender)", "Ploaj"]
__url__ = ["https://gitlab.com/Worldblender/io_scene_numdlb"]
__version__ = "0.1"
__bpydoc__ = """\
"""

bl_info = {
    "name": "Super Smash Bros. Ultimate Animation Importer",
    "description": "Imports animation data from NUANMB files (binary model format used by some games developed by Bandai-Namco)",
    "author": "Richard Qian (Worldblender), Ploaj",
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

def readVarLenString(file):
    nameBuffer = []
    while('\x00' not in nameBuffer):
        nameBuffer.append(str(file.read(1).decode("utf-8", "ignore")))
    del nameBuffer[-1]
    return ''.join(nameBuffer)

def importAnimations(context, filepath, import_method="create_new", auto_rotate=False):
    AnimName = ""
    FrameCount = 0
    BoneCount = 0
    BoneArray = []
    Animations_Array = []
    BoneTrsArray; BoneTrsArray = []
    
    if os.path.isfile(filepath):
        with open(filepath, 'rb') as am:
            am.seek(0x10, 0)
            AnimCheck = struct.unpack('<L', am.read(4))[0]
            if (AnimCheck == 0x414E494D):
                AnimVerA = struct.unpack('<H', am.read(2))[0]
                AnimVerB = struct.unpack('<H', am.read(2))[0]
                FrameCount = struct.unpack('<f', am.read(4))[0]
                Unk1 = struct.unpack('<H', am.read(2))[0]
                Unk2 = struct.unpack('<H', am.read(2))[0]
                AnimNameOff = am.tell() + struct.unpack('<L', am.read(4))[0]
                
                am.seek(AnimNameOff, 0)
                AnimName = readVarLenString(am); am.seek(0x04, 1)
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
        
        # Rotate armature if option is enabled
#        if auto_rotate:
#            bpy.ops.object.select_all(action='TOGGLE')
#            bpy.ops.object.select_pattern(pattern="*Armature*")
#            bpy.ops.transform.rotate(value=math.radians(90), axis=(1, 0, 0), constraint_axis=(True, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
#            bpy.ops.object.select_all(action='TOGGLE')

# ==== Import OPERATOR ====
from bpy_extras.io_utils import (ImportHelper)

class NUANMB_Import_Operator(bpy.types.Operator, ImportHelper):
    """Imports animation data from NUANMB files"""
    bl_idname = ("screen.nuanmb_import")
    bl_label = ("NUANMB Import")
    filename_ext = ".nuanmb"
    filter_glob = bpy.props.StringProperty(default="*.nuanmb", options={'HIDDEN'})
    
    import_method = bpy.props.EnumProperty(
            name="Import Method",
            description="How to import animations (when multiple are simulataneously imported",
            items=(("create_new", "Create new actions", "Animations will be imported as their own actions"),
                   ("append_existing", "Append to current", "Animations will be imported to the current action")),
            default="create_new",
            )

    auto_rotate = bpy.props.BoolProperty(
            name="Auto-Rotate Armature",
            description="Rotate the armature so that everything points up z-axis, instead of up y-axis",
            default=True,
            )

    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob", "auto_rotate"))
        importAnimations(context, **keywords)

        context.scene.update()
        return {"FINISHED"}

    @classmethod
    def poll(self, context):
        if context.active_object is not None:
            if context.active_object.type == 'ARMATURE':
                return True

            # Currently Disabled
            """
            elif context.active_object.parent is not None:
                return context.active_object.parent.type == 'ARMATURE'
            """

        return False

# Add to a menu
def menu_func_import(self, context):
    self.layout.operator(NUANMB_Import_Operator.bl_idname, text="NUANMB (.nuanmb)")

def register():
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.utils.register_module(__name__)

def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register
