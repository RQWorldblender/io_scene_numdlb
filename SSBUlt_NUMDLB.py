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
    "description": "Imports NUMDLB files (the Super Smash Bros. Ultimate Model model format, may be used by other games developed by Bandai-Namco)",
    "author": "Richard Qian (Worldblender), Random Talking Bush", "Ploaj",
    "version": (0,1),
    "blender": (2, 7, 0),
    "api": 31236,
    "location": "File > Import",
    "warning": '', # used for warning icon and text in addons panel
    "wiki_url": "https://gitlab.com/Worldblender/io_scene_numdlb",
    "tracker_url": "https://gitlab.com/Worldblender/io_scene_numdlb/issues",
    "category": "Import-Export"}

import bmesh, bpy, bpy_extras, mathutils, os, os.path, struct, string, sys, time
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
    pass

class MatStruct:
    pass

def importNUMDLB(self, context):
    BoneCount = 0
    MODLGrp_array = []
    Materials_array = []
    BoneArray = []
    BoneFixArray = []
    BoneTrsArray = []
    BoneParent_array = []
    BoneName_array = []
    PolyGrp_array = []
    WeightGrp_array = []
    
    MDLName = os.path.splitext((os.path.basename(filepath)))[0]
    with open(MDLName, 'rb') as md:
        #p = getFilenamePath MDLName
        #struct MODLStruct (MSHGrpName, MSHMatName)
            
        md.seek(0x10) #seek_set
        # Reads the model file to find information about the other files
        MODLCheck = unpack('L', md)
        if (MODLCheck == 0x4D4F444C):
            MODLVerA = unpack('H', md) #unsigned
            MODLVerB = unpack('H', md) #unsigned
            MODLNameOff = md.tell() + unpack('L', md); md.seek(0x04) #seek_cur
            SKTNameOff = md.tell() + unpack('L', md); md.seek(0x04) #seek_cur
            MATNameOff = md.tell() + unpack('L', md); md.seek(0x04) #seek_cur
            md.seek(0x10) #seek_cur
            MSHNameOff = md.tell() + unpack('L', md); md.seek(0x04) #seek_cur
            MSHDatOff = md.tell() + unpack('L', md); md.seek(0x04) #seek_cur
            MSHDatCount = unpack('L', md)
            md.seek(SKTNameOff) #seek_set
            SKTName = (p + readstring md)
            md.seek(MATNameOff) #seek_set
            MATNameStrLen = unpack('L', md); md.seek(0x04) #seek_cur
            MATName = (p + readstring md)
            md.seek(MSHNameOff) #seek_set
            MSHName = (p + readstring md); md.seek(0x04) #seek_cur
            md.seek(MSHDatOff) #seek_set
            for g in range(MSHDatCount):
                MSHGrpNameOff = md.tell() + unpack('L', md); md.seek(0x04) #seek_cur
                MSHUnkNameOff = md.tell() + unpack('L', md); md.seek(0x04) #seek_cur
                MSHMatNameOff = md.tell() + unpack('L', md); md.seek(0x04) #seek_cur
                MSHRet = md.tell()
                md.seek(MSHGrpNameOff) #seek_set
                MSHGrpName = md.readline()
                md.seek(MSHMatNameOff) #seek_set
                MSHMatName = md.readline()
                # MODLGrp_array.append(MODLStruct MSHGrpName:MSHGrpName MSHMatName:MSHMatName)
                md.seek(MSHRet) #seek_set
            #print(MODLGrp_array)
        
        # Imports the materials
        with open(MATName, 'rb') as mt:
            # struct MatStruct (MatName, MatColName, MatCol2Name, MatBakeName, MatNorName, MatEmiName, atEmi2Name, MatPrmName, MatEnvName)
            
            mt.seek(0x10) #seek_set
            MATCheck = unpack('L', mt)
            if (MATCheck == 0x4D41544C):
                MATVerA = unpack('H', mt) #unsigned
                MATVerB = unpack('H', mt) #unsigned
                MATHeadOff = mt.tell() + unpack('L', mt); mt.seek(0x04) #seek_cur
                MATCount = unpack('L', mt); mt.seek(0x04) #seek_cur
                mt.seek(MATHeadOff) #seek_set
                for m in range(MATCount):
                    MatColName = ""
                    MatCol2Name = ""
                    MatBakeName = ""
                    MatNorName = ""
                    MatEmiName = ""
                    MatEmi2Name = ""
                    MatPrmName = ""
                    MatEnvName = ""
                    MATNameOff = mt.tell() + unpack('L', mt); mt.seek(0x04) #seek_cur
                    MATParamGrpOff = mt.tell() + unpack('L', mt); mt.seek(0x04) #seek_cur
                    MATParamGrpCount = unpack('L', mt); mt.seek(0x04) #seek_cur
                    MATShdrNameOff = mt.tell() + unpack('L', mt); mt.seek(0x04) #seek_cur
                    MATRet = mt.tell()
                    mt.seek(MATNameOff) #seek_set
                    MatName = mt.readline()
                    print("Textures for " + MatName + ":")
                    mt.seek(MATParamGrpOff) #seek_set
                    for p in range(MATParamGrpCount):
                        MatParamID = unpack('L', mt); mt.seek(0x04) #seek_cur
                        MatParamOff = mt.tell() + unpack('L', mt); mt.seek(0x04) #seek_cur
                        MatParamType = unpack('L', mt); mt.seek(0x04) #seek_cur
                        MatParamRet = mt.tell()
                        if (MatParamType == 0x0B):
                            mt.seek(MatParamOff + 0x08) #seek_set
                            TexName = mt.readline()
                            # print("(" + bit.intAsHex(MatParamID) + ") for " + TexName)
                            case MatParamID of(
                                #default:(print("Unknown type (" + bit.intAsHex(MatParamID) as string + ") for " + TexName as string))
                                0x5C:(MatColName = TexName)
                                0x5D:(MatCol2Name = TexName)
                                0x5F:(MatBakeName = TexName)
                                0x60:(MatNorName = TexName)
                                0x61:(MatEmiName = TexName; if MatColName == "" do(MatColName = TexName))
                                0x62:(MatPrmName = TexName)
                                0x63:(MatEnvName = TexName)
                                0x65:(MatBakeName = TexName)
                                0x66:(MatColName = TexName)
                                0x67:(MatCol2Name = TexName)
                                0x6A:(MatEmi2Name = TexName; if MatCol2Name == "" do(MatCol2Name = TexName))
                                0x133:() # "noise_for_warp"
                            )
                            mt.seek(MatParamRet) #seek_set

                    print("-----")
                    # Materials_array.append(MatStruct MatName:MatName MatColName:MatColName MatCol2Name:MatCol2Name MatBakeName:MatBakeName MatNorName:MatNorName MatEmiName:MatEmiName MatEmi2Name:MatEmi2Name MatPrmName:MatPrmName MatEnvName:MatEnvName)
                    fseek mt MATRet #seek_set
                )
            )
                multimat = MultiMaterial()
                multimat.name = "SSBUMesh"
                multimat.numsubs = MATCount
                for m = 1 to MATCount do(
                mat = multimat.materialList[m]
                mat.name = Materials_array[m].MatName
                mat.showinviewport = true
                mat.twosided = false
                tm = Bitmaptexture filename:(p + (Materials_array[m].MatColName as string) + ".png")
                tm.alphasource = 0
                mat.diffuseMap = tm
                mat.opacityMap = tm
                mat.opacityMap.monoOutput = 1
                )
            fclose mt
            print(Materials_array)
        )

        # Imports the skeleton
        with open(SKTName, 'rb') as b:
            b.seek(0x10) #seek_set
            BoneCheck = unpack('L', b)
            if (BoneCheck == 0x534B454C):
                b.seek(0x18) #seek_set
                BoneOffset = b.tell() + unpack('L', b); b.seek(0x04) #seek_cur
                BoneCount = unpack('L', b); b.seek(0x04) #seek_cur
                BoneMatrOffset = b.tell() + unpack('L', b); b.seek(0x04) #seek_cur
                BoneMatrCount = unpack('L', b); b.seek(0x04) #seek_cur
                BoneInvMatrOffset = b.tell() + unpack('L', b); b.seek(0x04) #seek_cur
                BoneInvMatrCount = unpack('L', b); b.seek(0x04) #seek_cur
                BoneRelMatrOffset = b.tell() + unpack('L', b); b.seek(0x04) #seek_cur
                BoneRelMatrCount = unpack('L', b); b.seek(0x04) #seek_cur
                BoneRelMatrInvOffset = b.tell() + unpack('L', b); b.seek(0x04) #seek_cur
                BoneRelMatrInvCount = unpack('L', b); b.seek(0x04) #seek_cur
                b.seek(BoneOffset) #seek_set

                for c in range(BoneCount):
                    BoneNameOffset = b.tell() + unpack('L', b); b.seek(0x04) #seek_cur
                    BoneRet = b.tell()
                    b.seek(BoneNameOffset) #seek_set
                    BoneName = b.readline()
                    b.seek(BoneRet) #seek_set
                    BoneID = unpack('H', b)
                    BoneParent = unpack('H', b) + 1
                    BoneUnk = unpack('L', b)
                    BoneParent_array.append(BoneParent)
                    BoneName_array.append(BoneName)

                b.seek(BoneMatrOffset) #seek_set

                for c in range(BoneCount):
                    m11 = readfloat b; m12 = readfloat b; m13 = readfloat b; m14 = readfloat b
                    m21 = readfloat b; m22 = readfloat b; m23 = readfloat b; m24 = readfloat b
                    m31 = readfloat b; m32 = readfloat b; m33 = readfloat b; m34 = readfloat b
                    m41 = readfloat b; m42 = readfloat b; m43 = readfloat b; m44 = readfloat b
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
                for x = 1 to BoneFixArray.count do(
                    select BoneArray[BoneFixArray[x]]
                    $.parent = BoneArray[BoneParent_array[BoneFixArray[x]]]
                )
            )
        )

        # Imports the meshes
        with open(MSHName, 'rb') as f:
            time_start = time.time()

            # struct weight_data (boneids, weights)
            # struct PolyGrpStruct (VisGrpName, SingleBindName, FacepointCount, FacepointStart, FaceLongBit, VertCount, VertStart, VertStride, UVStart, UVStride, BuffParamStart, BuffParamCount)
            #struct WeightGrpStruct (GrpName, SubGroupNum, WeightInfMax, WeightFlag2, WeightFlag3, WeightFlag4, RigInfOffset, RigInfCount)

            f.seek(0x10) #seek_set
            MSHCheck = unpack('L', f)
            if (MSHCheck == 0x4D455348):
                f.seek(0x88) #seek_set
                PolyGrpInfOffset = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
                PolyGrpCount = unpack('L', f); f.seek(0x04) #seek_cur
                UnkOffset1 = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
                UnkCount1 = unpack('L', f); f.seek(0x04) #seek_cur
                FaceBuffSizeB = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
                VertBuffOffset = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
                UnkCount2 = unpack('L', f); f.seek(0x04) #seek_cur
                FaceBuffOffset = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
                FaceBuffSize = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
                WeightBuffOffset = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
                WeightCount = unpack('L', f); f.seek(0x04) #seek_cur

                f.seek(PolyGrpInfOffset) #seek_set
                for g in range(PolyGrpCount):
                    VisGrpNameOffset = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
                    f.seek(0x04) #seek_cur
                    Unk1 = unpack('L', f)
                    SingleBindNameOffset = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
                    VertCount = unpack('L', f)
                    FacepointCount = unpack('L', f)
                    Unk2 = unpack('L', f) # Always 3?
                    VertStart = unpack('L', f)
                    UVStart = unpack('L', f)
                    UnkOff1 = unpack('L', f)
                    Unk3 = unpack('L', f) # Always 0?
                    VertStride = unpack('L', f)
                    UVStride = unpack('L', f)
                    Unk4 = unpack('L', f) # Either 0 or 32
                    Unk5 = unpack('L', f) # Always 0
                    FacepointStart = unpack('L', f)
                    Unk6 = unpack('L', f) # Always 4
                    FaceLongBit = unpack('L', f) # Either 0 or 1
                    Unk8 = unpack('L', f) # Either 0 or 1
                    SortPriority = unpack('L', f)
                    Unk9 = unpack('L', f) # 0, 1, 256 or 257
                    fseek f 0x64 #seek_cur # A bunch of unknown float values.
                    BuffParamStart = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
                    BuffParamCount = unpack('L', f)
                    Unk10 = unpack('L', f) # Always 0
                    PolyGrpRet = f.tell()
                    fseek f VisGrpNameOffset #seek_set
                    VisGrpName = readstring f
                    fseek f SingleBindNameOffset #seek_set
                    SingleBindName = readstring f
                        append PolyGrp_array (PolyGrpStruct VisGrpName:VisGrpName SingleBindName:SingleBindName FacepointCount:FacepointCount FacepointStart:FacepointStart FaceLongBit:FaceLongBit VertCount:VertCount VertStart:VertStart VertStride:VertStride UVStart:UVStart UVStride:UVStride BuffParamStart:BuffParamStart BuffParamCount:BuffParamCount)
                    print(VisGrpName as string + " unknowns: 1: " + Unk1 as string + " | Off1: " + UnkOff1 as string + " | 2: " + Unk2 as string + " | 3: " + Unk3 as string + " | 4: " + Unk4 as string + " | 5: " + Unk5 as string + " | 6: " + Unk6 as string + " | LongFace: " + FaceLongBit as string + " | 8: " + Unk8 as string + " | Sort: " + SortPriority as string + " | 9: " + Unk9 as string + " | 10: " + Unk10 as string)
                    fseek f PolyGrpRet #seek_set
                )
                print(PolyGrp_array)

                fseek f VertBuffOffset #seek_set
                VertOffStart = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
                VertBuffSize = unpack('L', f); f.seek(0x04) #seek_cur
                UVOffStart = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
                UVBuffSize = unpack('L', f); f.seek(0x04) #seek_cur
                    
                fseek f WeightBuffOffset #seek_set
                    
					for b = 1 to WeightCount do(
						GrpNameOffset = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
						SubGroupNum = unpack('L', f); f.seek(0x04) #seek_cur
						WeightInfMax = readbyte f #unsigned; WeightFlag2 = readbyte f #unsigned; WeightFlag3 = readbyte f #unsigned; WeightFlag4 = readbyte f #unsigned; f.seek(0x04) #seek_cur
						RigInfOffset = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
						RigInfCount = unpack('L', f); f.seek(0x04) #seek_cur
						WeightRet = f.tell()
						fseek f GrpNameOffset #seek_set
						GrpName = readstring f
						append WeightGrp_array (WeightGrpStruct GrpName:GrpName SubGroupNum:SubGroupNum WeightInfMax:WeightInfMax WeightFlag2:WeightFlag2 WeightFlag3:WeightFlag3 WeightFlag4:WeightFlag4 RigInfOffset:RigInfOffset RigInfCount:RigInfCount)
						fseek f WeightRet #seek_set
					)
					print(WeightGrp_array)

					for p = 1 to PolyGrpCount do(
						Vert_array = #()
						Normal_array = #()
						Color_array = #(); Color2_array = #(); Color3_array = #(); Color4_array = #(); Color5_array = #()
						Alpha_array = #(); Alpha2_array = #(); Alpha3_array = #(); Alpha4_array = #(); Alpha5_array = #()
						UV_array = #(); UV2_array = #(); UV3_array = #(); UV4_array = #(); UV5_array = #()
						Face_array = #()
						Weight_array = #()
						SingleBindID = 0

						fseek f PolyGrp_array[p].BuffParamStart #seek_set
						
						PosFmt = 0; NormFmt = 0; TanFmt = 0; ColorCount = 0; UVCount = 0
						
						for v = 1 to PolyGrp_array[p].BuffParamCount do(
							BuffParamType = unpack('L', f)
							BuffParamFmt = unpack('L', f) + 1 # Adding one so that "0" counts as "none".
							BuffParamSet = unpack('L', f)
							BuffParamOffset = unpack('L', f)
							BuffParamLayer = unpack('L', f)
							BuffParamUnk1 = unpack('L', f) # always 0?
							BuffParamStrOff1 = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
							BuffParamStrOff2 = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
							BuffParamUnk2 = unpack('L', f) # always 1?
							BuffParamUnk3 = unpack('L', f) # always 0?
							BuffParamRet = f.tell()
							fseek f BuffParamStrOff2 #seek_set
							BuffNameOff = f.tell() + unpack('L', f); f.seek(0x04) #seek_set
							fseek f BuffNameOff #seek_set
							BuffName = readstring f
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
							fseek f BuffParamRet #seek_set
						)

						fseek f (VertOffStart + PolyGrp_array[p].VertStart) #seek_set

						print("Vert start: " + (ftell f as string))
						for v = 1 to PolyGrp_array[p].VertCount do(
							case PosFmt of(
								default: ("Unknown position format!")
								1:(
									vx = readfloat f
									vy = readfloat f
									vz = readfloat f
									append Vert_array [vx,vy,vz]
								)
							)
							case NormFmt of(
								default: ("Unknown normals format!")
								6:(
									nx = readhalffloat f * 2 
									ny = readhalffloat f * 2
									nz = readhalffloat f * 2
									nq = readhalffloat f * 2
									append Normal_array [nx,ny,nz]
								)
							)
							case TanFmt of(
								default: ("Unknown tangents format!")
								6:(
									tanx = readhalffloat f * 2
									tany = readhalffloat f * 2
									tanz = readhalffloat f * 2
									tanq = readhalffloat f * 2
								)
							)
						)
						print("Vert end: " + (ftell f as string))

						fseek f (UVOffStart + PolyGrp_array[p].UVStart) #seek_set

						print("UV start: " + (ftell f as string))
						for v = 1 to PolyGrp_array[p].VertCount do(
							case UVCount of(
								default: (throw ("More than 5 UV sets, crashing gracefully."))
								0:(
									append UV_array [0,0,0]
								)
								1:(
									tu = (readhalffloat f * 2)
									tv = ((readhalffloat f * 2) * -1) + 1
									append UV_array [tu,tv,0]
								)
								2:(
									tu = (readhalffloat f * 2)
									tv = ((readhalffloat f * 2) * -1) + 1
									tu2 = (readhalffloat f * 2)
									tv2 = ((readhalffloat f * 2) * -1) + 1
									append UV_array [tu,tv,0]
									append UV2_array [tu2,tv2,0]
								)
								3:(
									tu = (readhalffloat f * 2)
									tv = ((readhalffloat f * 2) * -1) + 1
									tu2 = (readhalffloat f * 2)
									tv2 = ((readhalffloat f * 2) * -1) + 1
									tu3 = (readhalffloat f * 2)
									tv3 = ((readhalffloat f * 2) * -1) + 1
									append UV_array [tu,tv,0]
									append UV2_array [tu2,tv2,0]
									append UV3_array [tu3,tv3,0]
								)
								4:(
									tu = (readhalffloat f * 2)
									tv = ((readhalffloat f * 2) * -1) + 1
									tu2 = (readhalffloat f * 2)
									tv2 = ((readhalffloat f * 2) * -1) + 1
									tu3 = (readhalffloat f * 2)
									tv3 = ((readhalffloat f * 2) * -1) + 1
									tu4 = (readhalffloat f * 2)
									tv4 = ((readhalffloat f * 2) * -1) + 1
									append UV_array [tu,tv,0]
									append UV2_array [tu2,tv2,0]
									append UV3_array [tu3,tv3,0]
									append UV4_array [tu4,tv4,0]
								)
								5:(
									tu = (readhalffloat f * 2)
									tv = ((readhalffloat f * 2) * -1) + 1
									tu2 = (readhalffloat f * 2)
									tv2 = ((readhalffloat f * 2) * -1) + 1
									tu3 = (readhalffloat f * 2)
									tv3 = ((readhalffloat f * 2) * -1) + 1
									tu4 = (readhalffloat f * 2)
									tv4 = ((readhalffloat f * 2) * -1) + 1
									tu5 = (readhalffloat f * 2)
									tv5 = ((readhalffloat f * 2) * -1) + 1
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
									colorr = readbyte f #unsigned
									colorg = readbyte f #unsigned
									colorb = readbyte f #unsigned
									colora = (readbyte f #unsigned as float) / 128
									append Color_array [colorr,colorg,colorb]; append Alpha_array colora
								)
								2:(
									colorr = readbyte f #unsigned
									colorg = readbyte f #unsigned
									colorb = readbyte f #unsigned
									colora = (readbyte f #unsigned as float) / 128
									colorr2 = readbyte f #unsigned
									colorg2 = readbyte f #unsigned
									colorb2 = readbyte f #unsigned
									colora2 = (readbyte f #unsigned as float) / 128
									append Color_array [colorr,colorg,colorb]; append Alpha_array colora
									append Color2_array [colorr2,colorg2,colorb2]; append Alpha2_array colora2
								)
								3:(
									colorr = readbyte f #unsigned
									colorg = readbyte f #unsigned
									colorb = readbyte f #unsigned
									colora = (readbyte f #unsigned as float) / 128
									colorr2 = readbyte f #unsigned
									colorg2 = readbyte f #unsigned
									colorb2 = readbyte f #unsigned
									colora2 = (readbyte f #unsigned as float) / 128
									colorr3 = readbyte f #unsigned
									colorg3 = readbyte f #unsigned
									colorb3 = readbyte f #unsigned
									colora3 = (readbyte f #unsigned as float) / 128
									append Color_array [colorr,colorg,colorb]; append Alpha_array colora
									append Color2_array [colorr2,colorg2,colorb2]; append Alpha2_array colora2
									append Color3_array [colorr3,colorg3,colorb3]; append Alpha3_array colora3
								)
								4:(
									colorr = readbyte f #unsigned
									colorg = readbyte f #unsigned
									colorb = readbyte f #unsigned
									colora = (readbyte f #unsigned as float) / 128
									colorr2 = readbyte f #unsigned
									colorg2 = readbyte f #unsigned
									colorb2 = readbyte f #unsigned
									colora2 = (readbyte f #unsigned as float) / 128
									colorr3 = readbyte f #unsigned
									colorg3 = readbyte f #unsigned
									colorb3 = readbyte f #unsigned
									colora3 = (readbyte f #unsigned as float) / 128
									colorr4 = readbyte f #unsigned
									colorg4 = readbyte f #unsigned
									colorb4 = readbyte f #unsigned
									colora4 = (readbyte f #unsigned as float) / 128
									append Color_array [colorr,colorg,colorb]; append Alpha_array colora
									append Color2_array [colorr2,colorg2,colorb2]; append Alpha2_array colora2
									append Color3_array [colorr3,colorg3,colorb3]; append Alpha3_array colora3
									append Color4_array [colorr4,colorg4,colorb4]; append Alpha4_array colora4
								)
								5:(
									colorr = readbyte f #unsigned
									colorg = readbyte f #unsigned
									colorb = readbyte f #unsigned
									colora = (readbyte f #unsigned as float) / 128
									colorr2 = readbyte f #unsigned
									colorg2 = readbyte f #unsigned
									colorb2 = readbyte f #unsigned
									colora2 = (readbyte f #unsigned as float) / 128
									colorr3 = readbyte f #unsigned
									colorg3 = readbyte f #unsigned
									colorb3 = readbyte f #unsigned
									colora3 = (readbyte f #unsigned as float) / 128
									colorr4 = readbyte f #unsigned
									colorg4 = readbyte f #unsigned
									colorb4 = readbyte f #unsigned
									colora4 = (readbyte f #unsigned as float) / 128
									colorr5 = readbyte f #unsigned
									colorg5 = readbyte f #unsigned
									colorb5 = readbyte f #unsigned
									colora5 = (readbyte f #unsigned as float) / 128
									append Color_array [colorr,colorg,colorb]; append Alpha_array colora
									append Color2_array [colorr2,colorg2,colorb2]; append Alpha2_array colora2
									append Color3_array [colorr3,colorg3,colorb3]; append Alpha3_array colora3
									append Color4_array [colorr4,colorg4,colorb4]; append Alpha4_array colora4
									append Color5_array [colorr5,colorg5,colorb5]; append Alpha5_array colora5
								)
							)
						)
						print("UV end: " + (ftell f as string))

						fseek f (FaceBuffOffset + PolyGrp_array[p].FacepointStart) #seek_set
						print("Face start: " + (ftell f as string))
						for fc = 1 to (PolyGrp_array[p].FacepointCount / 3) do(
							case PolyGrp_array[p].FaceLongBit of(
								default:(throw("Unknown face bit value!"))
								0:(
										fa = readshort f #unsigned + 1
										fb = readshort f #unsigned + 1
										fc = readshort f #unsigned + 1
										append Face_array [fa,fb,fc]
								)
								1:(
										fa = unpack('L', f) #unsigned + 1
										fb = unpack('L', f) #unsigned + 1
										fc = unpack('L', f) #unsigned + 1
										append Face_array [fa,fb,fc]
								)
							)
						)
						print("Face end: " + (ftell f as string))

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
								append Weight_array (weight_data boneids:#() weights:#())
							)
							RigSet = 1
							for b = 1 to WeightGrp_array.count do(
								if PolyGrp_array[p].VisGrpName == WeightGrp_array[b].GrpName do(
									RigSet = b
									WeightGrp_array[b].GrpName = "" # Dumb fix due to shared group names but split entries, prevents crashing.
									exit
								)
							)

							fseek f WeightGrp_array[RigSet].RigInfOffset #seek_set
							print("Rig info start: " + f.tell() as string)

							if WeightGrp_array[RigSet].RigInfCount != 0 then (
								for x = 1 to WeightGrp_array[RigSet].RigInfCount do(
									RigBoneNameOffset = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
									RigBuffStart = f.tell() + unpack('L', f); f.seek(0x04) #seek_cur
									RigBuffSize = unpack('L', f); f.seek(0x04) #seek_cur
									RigRet = f.tell()
									fseek f RigBoneNameOffset #seek_set
									RigBoneName = readstring f
									fseek f RigBuffStart #seek_set
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
										RigVertID = readshort f + 1
										RigValue = readfloat f
										append Weight_array[RigVertID].boneids RigBoneID
										append Weight_array[RigVertID].weights RigValue
									)
									fseek f RigRet #seek_set
								) 
							) else (
								print (PolyGrp_array[p].VisGrpName + " has no influences! Treating as a root singlebind instead.")
								Weight_array = #()
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
						if use_vertex_colors == True then (
							setNumCPVVerts msh msh.numTVerts
							setCVertMode msh true
							setShadeCVerts msh true
						)
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
						if use_vertex_colors == True do(
							for j = 1 to Color_array.count do setvertcolor msh j Color_array[j]
							for j = 1 to Alpha_array.count do(meshop.setVertAlpha msh -2 j Alpha_array[j])
						)
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
							boneIDMap = #()
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
								bi = #() --bone index array
								wv = #() --weight value array
								
								for j = 1 to w.boneids.count do
								(
									boneid = w.boneids[j]
									weight = w.weights[j]
									append bi boneIDMap[boneid]
									append wv weight
								)
								skinOps.ReplaceVertexWeights skinMod i bi wv
							)

						)
					)
				)
				fclose f
				print("Done! ("+((((time.time())-time_start)*0.001))+" Seconds)")
			)

		)
	)

)

CreateDialog ModelImporter

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

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "extra_tex_path")
    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob",))
        loadSPM(context, **keywords)
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

