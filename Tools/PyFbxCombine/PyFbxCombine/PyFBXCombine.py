import sys

import json
import os
import numpy as np
from objloader import Obj
from fbx import *
import FbxCommon
from operator import index
from test.test_importlib.import_.test_fromlist import ReturnValue
from functools import cmp_to_key


def GetAbsoluteRootPath():
    result = os.path.dirname(os.path.realpath(__file__))
    return result

def GetTestObjFilePath():
    ret = GetAbsoluteRootPath() + "/../../../res3/save_obj_new/xudong_mesh.obj"
    ret = os.path.abspath(ret)
    return ret

def GetTestVertexBoneDataPath():
    ret = GetAbsoluteRootPath() + "/../../../res3/save_obj_new/xudong_mesh.npy"
    ret = os.path.abspath(ret)
    return ret

def GetTestSkeleteLinkPath():
    ret = GetAbsoluteRootPath() + "/../../../res3/save_obj_new/xudong_mesh_parents.npy"
    ret = os.path.abspath(ret)
    return ret

def GetTestBoneDataPath():
    ret = GetAbsoluteRootPath() + "/../../../res3/save_obj_new/xudong_mesh_joints.npy"
    ret = os.path.abspath(ret)
    return ret

def GetOrCreateLayerFromMesh(mesh: FbxMesh, layerIndex: int = 0):
    layerCount = mesh.GetLayerCount()
    if layerIndex >= layerCount:
        for i in range(layerCount, layerIndex + 1, 1):
            mesh.CreateLayer()
    return mesh.GetLayer(layerIndex)

def CreateMesh(scene, meshName, vertexs, normals, texcoords, faces)->FbxMesh:
    rootNode = scene.GetRootNode()
    currentNode = FbxNode.Create(scene, meshName)

    mesh: FbxMesh = FbxMesh.Create(scene, meshName)

    ## 顶点
    vertexNum = len(vertexs)
    mesh.InitControlPoints(vertexNum)
    for idx in range(0, vertexNum, 1):
        vert = FbxVector4(vertexs[idx][0], vertexs[idx][1], vertexs[idx][2])
        mesh.SetControlPointAt(vert, idx)
    ## subMesh(IndexBuffer), 有可能有多个subMesh的
    faceNum = len(faces)
    idx = 0
    faceSubIdx = 0
    while idx < faceNum:
        face1 = faces[idx]
        idx += 1
        face2 = faces[idx]
        idx += 1
        face3 = faces[idx]
        idx += 1
        # 顶点索引
        mesh.BeginPolygon()
        ## 从1开始的，转成从0开始
        mesh.AddPolygon(face1[faceSubIdx] - 1)
        mesh.AddPolygon(face2[faceSubIdx] - 1)
        mesh.AddPolygon(face3[faceSubIdx] - 1)
        mesh.EndPolygon()
    faceSubIdx += 1
    ## 法线
    normalNum = len(normals)
    if normalNum > 0:
        normalElement: FbxLayerElementNormal = FbxLayerElementNormal.Create(mesh, "normal")
        normalElement.SetMappingMode(FbxLayerElement.EMappingMode.eByControlPoint)
        normalElement.SetReferenceMode(FbxLayerElement.EReferenceMode.eDirect) # eDirect直接使用VertexIndex，只要填充数据即可， eIndexToDirect还需要填充Normal Index
        arr = normalElement.GetDirectArray()
        arr.Resize(normalNum)
        for i in range(0, normalNum, 1):
            arr.SetAt(i, FbxVector4(normals[i][0], normals[i][1], normals[i][2], 1.0))
        layer: FbxLayer = GetOrCreateLayerFromMesh(mesh)
        layer.SetNormals(normalElement)
        faceSubIdx += 1
    ## UV
    uvNum = len(texcoords)
    if uvNum > 0:
        uvElement: FbxLayerElementUV = mesh.CreateElementUV("Diffuse")
        uvElement.SetMappingMode(FbxLayerElement.EMappingMode.eByControlPoint)
        uvElement.SetReferenceMode(FbxLayerElement.EReferenceMode.eDirect)
        arr = uvElement.GetDirectArray()
        arr.Resize(uvNum)
        for i in range(0, uvNum, 1):
            arr.SetAt(i, FbxVector2(texcoords[i][0], texcoords[i][1]))
        layer: FbxLayer = GetOrCreateLayerFromMesh(mesh)
        layer.SetUVs(uvElement)
        faceSubIdx += 1

    mesh.BuildMeshEdgeArray() # 生成边界数组
    currentNode.AddNodeAttribute(mesh)

    rootNode.AddChild(currentNode)
    return mesh, currentNode

def _CreateFbxBoneNode(fbxManager, node)->FbxNode:
    boneName = node["name"]
    isRoot = not ("parent" in node)
    skel: FbxSkeleton = FbxSkeleton.Create(fbxManager, boneName)
    if isRoot:
        skel.SetSkeletonType(FbxSkeleton.EType.eRoot)
    else:
        skel.SetSkeletonType(FbxSkeleton.EType.eLimbNode)
    fbxNode: FbxNode = FbxNode.Create(fbxManager, boneName)
    fbxNode.SetNodeAttribute(skel)
    if isRoot:
        position: FbxDouble3 = node["position"]
        fbxNode.LclTranslation.Set(position)
        if "rotation" in node:
            rot: FbxDouble3 = node["rotation"]
            print(rot[0])
            fbxNode.LclRotation.Set(rot[0])
        if "scale" in node:
            scale: FbxDouble3 = node["scale"]
            fbxNode.LclScaling.Set(scale[0])
    else:
        parentPosition: FbxDouble3 = node["parent"]["position"]
        position: FbxDouble3 = node["position"]
        offsetPos: FbxDouble3 = FbxDouble3(position[0] - parentPosition[0], position[1] - parentPosition[1], position[2] - parentPosition[2])
        fbxNode.LclTranslation.Set(offsetPos)
        if "rotation" in node:
            parentRot: FbxDouble3 = node["parent"]["rotation"][0]
            rot: FbxDouble3 = node["rotation"][0]
            fbxNode.LclRotation.Set(FbxDouble3(rot[0] - parentRot[0], rot[1] - parentRot[1], rot[2] - parentRot[2]))
        if "scale" in node:
            parentScale: FbxDouble3 = node["parent"]["scale"][0]
            scale: FbxDouble3 = node["scale"][0]
            fbxNode.LclScaling.Set(FbxDouble3(scale[0] - parentScale[0], scale[1] - parentScale[1], scale[2] - parentScale[2]))
    node["FbxNode"] = fbxNode
    #fbxNode.LclTranslation.Set(node["position"])
    return fbxNode

## 创建子FBX节点
def _CreateChildFbxBoneNode(fbxManager, targetFbxNode: FbxNode, targetNode):
    for child in targetNode["childs"]:
        childFbxNode: FbxNode = _CreateFbxBoneNode(fbxManager, child)
        targetFbxNode.AddChild(childFbxNode)
        _CreateChildFbxBoneNode(fbxManager, childFbxNode, child)
    return

global _cMinWeight
_cMinWeight = 0.001

def _CreateSkin(fbxManager, scene, mesh, meshNode, vertexBoneDatas, skelRootNode):
    rootFbxNode = skelRootNode["FbxNode"]
    clusterRoot: FbxCluster = FbxCluster.Create(fbxManager, "Cluster_" + skelRootNode["name"])
    clusterRoot.SetLink(rootFbxNode)
    clusterRoot.SetLinkMode(FbxCluster.ELinkMode.eAdditive)

    cluster_dict = {}
    N1 = len(vertexBoneDatas)
    VertexNum = None
    VertexBoneMap = {}
    f = open("output.log", "w")
    try:
        for i in range(0, N1, 1):
            boneWeightDatas = vertexBoneDatas[i]
            key = str(i)
            N2 = len(boneWeightDatas)
            VertexNum = N2
            for j in range(0, N2, 1):
                if abs(boneWeightDatas[j]) >= _cMinWeight:
                    if not j in VertexBoneMap:
                        VertexBoneMap[j] = []
                    item = {"boneName": key, "boneIndex":i, "boneWeight": boneWeightDatas[j]}
                    VertexBoneMap[j].append(item)

        for vertexIndex in VertexBoneMap:
            boneDatas: list = VertexBoneMap[vertexIndex]
            boneDatasNum = len(boneDatas)
            if boneDatasNum > 4:
                ## 排个序
                boneDatas.sort(key=cmp_to_key(lambda a, b: a["boneWeight"] - b["boneWeight"]), reverse=True)
                s = "[Error] VertexIndex: %d boneDataNum: %d === %s" % (vertexIndex, boneDatasNum, str(boneDatas))
                print(s)
                f.write(s + "\n")
                f.flush()
                ### 处理多余的蒙皮顶点数据，保证不会超过4个骨骼影响
                totalWeight = 0
                for idx in range(0, boneDatasNum):
                    totalWeight += boneDatas[idx]["boneWeight"]
                removeWeight = 0
                for idx in range(4, boneDatasNum):
                    removeWeight += boneDatas[idx]["boneWeight"]
                for idx in range(0, 4):
                    boneDatas[idx]["boneWeight"] = boneDatas[idx]["boneWeight"] + boneDatas[idx]["boneWeight"]/totalWeight * removeWeight
                for idx in range(4, boneDatasNum):
                    boneDatas.pop(len(boneDatas) - 1) ## 最后一个删除
                s = "[Fix] VertexIndex: %d boneDataNum: %d === %s" % (vertexIndex, len(boneDatas), str(boneDatas))
                print(s)
                f.write(s + "\n")
                f.flush()
                ########################

        ## 重新生成vertexBoneDatas
        newVertexBoneDatas = {}
        for vertexIndex in VertexBoneMap:
            boneDatas: list = VertexBoneMap[vertexIndex]
            boneDatasNum = len(boneDatas)
            for idx in range(0, boneDatasNum):
                boneIndex = boneDatas[idx]["boneIndex"]
                boneWeight = boneDatas[idx]["boneWeight"]
                if not boneIndex in newVertexBoneDatas:
                    newVertexBoneDatas[boneIndex] = {}
                item = {"vertexIndex": vertexIndex, "boneWeight": boneWeight}
                newVertexBoneDatas[boneIndex][vertexIndex] = item
        vertexBoneDatas = []
        for boneIndex in range(0, N1, 1):
            lst = []
            vertexBoneDatas.append(lst)
            boneDatas = None
            if boneIndex in newVertexBoneDatas:
                boneDatas = newVertexBoneDatas[boneIndex]
            for vertexIndex in range(0, VertexNum):
                if boneDatas != None and vertexIndex in boneDatas:
                    lst.append(boneDatas[vertexIndex]["boneWeight"])
                else:
                    lst.append(0)
        ########################

        for i in range(0, N1, 1):
            boneWeightDatas = vertexBoneDatas[i]
            key = str(i)
            cluster_dict[key]: FbxCluster = FbxCluster.Create(fbxManager, "Cluster_" + key)
            fbxNode: FbxNode = scene.FindNodeByName(key)
            cluster_dict[key].SetLink(fbxNode)
            cluster_dict[key].SetLinkMode(FbxCluster.ELinkMode.eAdditive)
            N2 = len(boneWeightDatas)
            for j in range(0, N2, 1):
                if abs(boneWeightDatas[j]) >= 0.000001:
                    s = "vertexIndex: " + str(j) + " boneIndex " + key + " boneWeight: " + str(boneWeightDatas[j])
                    print(s)
                    f.write(s + "\n")
                    f.flush()
                    cluster_dict[key].AddControlPointIndex(j, boneWeightDatas[j])
    finally:
        f.close()
        f = None

    # Matrix
    mat = scene.GetAnimationEvaluator().GetNodeGlobalTransform(meshNode)
    clusterRoot.SetTransformMatrix(mat)
    for key in cluster_dict:
        cluster_dict[key].SetTransformMatrix(mat)

    mat = scene.GetAnimationEvaluator().GetNodeGlobalTransform(rootFbxNode)
    clusterRoot.SetTransformLinkMatrix(mat)

    for key in cluster_dict:
        mat = scene.GetAnimationEvaluator().GetNodeGlobalTransform(scene.FindNodeByName(key))
        cluster_dict[key].SetTransformLinkMatrix(mat)

    skin = FbxSkin.Create(fbxManager, "")
    skin.AddCluster(clusterRoot)
    for key in cluster_dict:
        skin.AddCluster(cluster_dict[key])

    mesh.AddDeformer(skin)
    return

def AddSkinnedDataToMesh(fbxManager, scene, mesh, meshNode, vertexBoneDatas, bonePosDatas, boneRotDatas, boneScaleDateas, boneLinkDatas):
    ## 骨骼KEY（字符串）和位置建立关系
    boneNum = len(bonePosDatas)
    if boneNum <= 0:
        return
    exportBoneMap = {} ## 骨骼名对应位置
    for i in range(0, boneNum, 1):
        bonePos = bonePosDatas[i]
        boneRot = None
        hasBoneRot = str(type(boneRotDatas)) != "<class 'NoneType'>"
        if hasBoneRot:
            boneRot = boneRotDatas[i]
        boneScale = None
        hasBoneScale = str(type(boneScaleDateas)) != "<class 'NoneType'>"
        if hasBoneScale:
            boneScale = boneScaleDateas[i]
        key = str(i)
        exportBoneMap[key] = {
            "position": FbxDouble3(bonePos[0], bonePos[1], bonePos[2]), # 位置(世界坐标系)
            "childs": [],
            "name": str(i), ## 骨骼名称
        }
        if hasBoneRot:
            node = exportBoneMap[key]
            node["rotation"] = FbxDouble3(boneRot[0], boneRot[1], boneRot[2]), # 角度制(世界坐标系)
        if hasBoneScale:
            node = exportBoneMap[key]
            node["scale"] = FbxDouble3(boneScale[0], boneScale[1], boneScale[2]), # 缩放(世界坐标系)
    ##### 拓扑关系
    boneLinkNum = len(boneLinkDatas)
    if boneLinkNum <= 0 or boneLinkNum != boneNum:
        return
    for i in range(0, boneLinkNum, 1):
        parentBoneIndex = boneLinkDatas[i]
        if parentBoneIndex >= 0:
            boneName = str(i)
            parentBoneName = str(parentBoneIndex)
            bone = exportBoneMap[boneName]
            parentBone = exportBoneMap[parentBoneName]
            bone["parent"] = parentBone
            parentBone["childs"].append(bone)

    removeList = []
    for key, value in exportBoneMap.items():
        if "parent" in value:
            removeList.append(key)
    for key in removeList:
        exportBoneMap.pop(key, None)
    ## 生成FbxSkeleton
    skelRootNode = None
    for key, value in exportBoneMap.items():
        skelRootNode = value
        fbxRootNode: FbxNode = _CreateFbxBoneNode(fbxManager, value)
        _CreateChildFbxBoneNode(fbxManager, fbxRootNode, value)
        scene.GetRootNode().GetChild(0).AddChild(fbxRootNode)
    ## 顶点蒙皮
    _CreateSkin(fbxManager, scene, mesh, meshNode, vertexBoneDatas, skelRootNode)
    ##
    return

global bUseSceneImport
bUseSceneImport = True

## obj模型 顶点BoneWeight 骨骼位置 骨骼父子关系 导出文件
def BuildFBXData(objFileName, vertBoneDataFileName, boneLocDataFileName, boneRotDataFileName, boneScaleDataFileName, skeleteLinkFileName, outFileName = "out.fbx"):
    if bUseSceneImport:
        manager, scene = FbxCommon.InitializeSdkObjects()
        FbxCommon.LoadScene(manager, scene, objFileName)
        scene.GetRootNode().GetChild(0).GetChild(0).SetName("Character")
        FbxGeometryConverter(manager).Triangulate(scene, True) #保证模型是三角形
        meshNode: FbxNode = scene.GetRootNode().GetChild(0).GetChild(0)
        attriNum = meshNode.GetNodeAttributeCount()
        mesh = None
        for i in range(attriNum):
            attribute = meshNode.GetNodeAttributeByIndex(i)
            attributeType = attribute.GetAttributeType()
            if attributeType == FbxNodeAttribute.EType.eMesh:
                mesh = attribute
                break
        if mesh == None:
            print("not found Mesh Attribute")
            return
        ## vertex骨骼信息
        vertexBoneDatas = np.load(vertBoneDataFileName)
        ## 骨骼关联信息
        boneLinkDatas = np.load(skeleteLinkFileName)
        ## 骨骼位置信息
        boneLocDatas = np.load(boneLocDataFileName)
        ## 骨骼旋转信息
        boneRotDatas = None
        if boneRotDataFileName != None:
            boneRotDatas = np.load(boneRotDataFileName)
        ## 骨骼缩放信息
        boneScaleDatas = None
        if boneScaleDataFileName != None:
            boneScaleDatas = np.load(boneScaleDataFileName)
        # 导入骨骼和蒙皮信息，让mesh变skinnedMesh
        # AddSkinnedDataToMesh(fbxManager, scene, mesh, meshNode, vertexBoneDatas, bonePosDatas, boneRotDatas, boneScaleDateas, boneLinkDatas)
        AddSkinnedDataToMesh(manager, scene, mesh, meshNode, vertexBoneDatas, boneLocDatas, boneRotDatas,
                            boneScaleDatas, boneLinkDatas)
    else:
        model = Obj.open(objFileName)
        ## 位置数据
        vertexs = np.array(model.vert)
        ## 法线
        normals = np.array(model.norm)
        ## 纹理坐标
        texcoords = np.array(model.text)
        ## 三角面索引列表
        faces = np.array(model.face)
        ## vertex骨骼信息
        vertexBoneDatas = np.load(vertBoneDataFileName)
        ## 骨骼关联信息
        boneLinkDatas = np.load(skeleteLinkFileName)
        ## 骨骼信息
        boneLocDatas = np.load(boneLocDataFileName)
        ## 骨骼旋转信息
        boneRotDatas = None
        if boneRotDataFileName != None:
            boneRotDatas = np.load(boneRotDataFileName)
        ## 骨骼缩放信息
        boneScaleDatas = None
        if boneScaleDataFileName != None:
            boneScaleDatas = np.load(boneScaleDataFileName)
        ## 初始化FBX环境
        manager, scene = FbxCommon.InitializeSdkObjects()
        # 创建Mesh
        mesh, meshNode = CreateMesh(scene, "Character", vertexs, normals, texcoords, faces)
        # 导入骨骼和蒙皮信息，让mesh变skinnedMesh
        AddSkinnedDataToMesh(manager, scene, mesh, meshNode, vertexBoneDatas, boneLocDatas, boneRotDatas,
                             boneScaleDatas, boneLinkDatas)
    ## 导出
    FbxCommon.SaveScene(manager, scene, outFileName)
    return

def Generate_Json_ToNPY(dir, name, extName):
    fileName = "%s/%s_%s.json" % (dir, name, extName)
    if not os.path.exists(fileName):
        print("not found: %s" % fileName)
        return
    f = open(fileName, "r")
    str = f.read()
    f.close()
    arr = json.loads(str)
    target = np.array(arr)
    idx = fileName.rfind(".")
    fileName = fileName[:idx] + ".npy"
    np.save(fileName, target)
    return

def Generate_JsonToNPY(dir, name):
    dir = os.path.abspath(dir)
    dir = dir.replace("\\", "/")
    print("[Generate_JsonToNPY] dir: %s, name: %s" % (dir, name))
    ## 位置
    print("[Generate] Convert Location to joints...")
    Generate_Json_ToNPY(dir, name, "joints")
    ## 旋转
    print("[Generate] Convert rot to rots...")
    Generate_Json_ToNPY(dir, name, "rots")
    ## 缩放
    print("[Generate] Convert scale to scales...")
    Generate_Json_ToNPY(dir, name, "scales")
    ## 骨骼关联
    print("[Generate] Convert boneLink to parents...")
    Generate_Json_ToNPY(dir, name, "parents")
    ## 骨骼顶点的权重
    print("[Generate] Convert boneWeight to mesh...")
    Generate_Json_ToNPY(dir, name, "mesh")
    return

# 使用obj文件和NPY文件生成FBX
def Generate_ObjAndNPY_ToFBX(dir, name):
    objFileName = "%s/%s.obj" % (dir, name)
    objFileName = os.path.abspath(objFileName)
    if not os.path.exists(objFileName):
        return
    vertexBoneFileName = "%s/%s_mesh.npy" % (dir, name)
    vertexBoneFileName = os.path.abspath(vertexBoneFileName)
    if not os.path.exists(vertexBoneFileName):
        return
    boneLocFileName = "%s/%s_joints.npy" % (dir, name)
    boneLocFileName = os.path.abspath(boneLocFileName)
    if not os.path.exists(boneLocFileName):
        return
    boneLinkeFileName = "%s/%s_parents.npy" % (dir, name)
    boneLinkeFileName = os.path.abspath(boneLinkeFileName)
    if not os.path.exists(boneLinkeFileName):
        return
    boneRotFileName = "%s/%s_rots.npy" % (dir, name)
    boneRotFileName = os.path.abspath(boneRotFileName)
    if not os.path.exists(boneRotFileName):
        boneRotFileName = None
    boneScaleFileName = "%s/%s_scales.npy" % (dir, name)
    boneScaleFileName = os.path.abspath(boneScaleFileName)
    if not os.path.exists(boneScaleFileName):
        boneScaleFileName = None
    ## BuildFBXData(objFileName, vertBoneDataFileName, boneLocDataFileName, boneRotDataFileName, boneScaleDataFileName, skeleteLinkFileName, outFileName = "out.fbx")
    BuildFBXData(objFileName, vertexBoneFileName, boneLocFileName, boneRotFileName, boneScaleFileName, boneLinkeFileName)
    return

def Main():
    argv = sys.argv
    if len(argv) >= 4:
        if argv[1] == "gen-npy":
            dir = str(argv[2])
            name = str(argv[3])
            Generate_JsonToNPY(dir, name)
        elif argv[1] == "gen-fbx":
            dir = str(argv[2])
            name = str(argv[3])
            Generate_ObjAndNPY_ToFBX(dir, name)
            return
        return
    print("no parameter: run default~!")
    ##print(type(None))
    #BuildFBXData(GetTestObjFilePath(), GetTestVertexBoneDataPath(), GetTestBoneDataPath(), None, None, GetTestSkeleteLinkPath())
    #Generate_ObjAndNPY_ToFBX("./example_json", "hero_kof_kyo_body_0002")
    #Generate_JsonToNPY("./example_json", "hero_kof_kyo_body_0002")
    return

##################################### 调用入口 ###################################
if __name__ == '__main__':
    Main()
#################################################################################