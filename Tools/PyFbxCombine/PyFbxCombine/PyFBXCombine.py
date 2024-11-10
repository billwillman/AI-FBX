import math
import sys
from math import degrees

import json
import os
import numpy as np
from objloader import Obj
from fbx import *
import FbxCommon
from operator import index
from test.test_importlib.import_.test_fromlist import ReturnValue
from functools import cmp_to_key
import Quaternion

### FbxExporter.cs ExportSkinnedMesh


def _HasAttribute(obj, name)->bool:
    ret = name in obj
    if ret:
        typeName = str(type(obj[name]))
        ret = typeName != "<class 'NoneType'>"
    return ret

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
    ### 设置跟UNITY一致
    currentNode.SetTransformationInheritType(FbxTransform.EInheritType.eInheritRSrs)
    currentNode.SetRotationOrder(FbxNode.EPivotSet.eSourcePivot, FbxEuler.EOrder.eOrderZXY)
    currentNode.SetRotationActive(True)
    ###

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

def _NormalDegree(degree: float)->float:
    if degree > 180.0:
        degree = degree - 360.0
    elif degree < -180.0:
        degree = degree + 360.0
    return degree
def _QuatToRollPitchYaw(quat: FbxQuaternion)->FbxDouble3:
    ## __init__(self, w, x, y, z):
    q = Quaternion.FQuat(quat[3], quat[0], quat[1], quat[2])
    ret = q.eulerAngles
    x = ret[0] if math.fabs(ret[0]) > 0.000001 else 0
    y = ret[1] if math.fabs(ret[1]) > 0.000001 else 0
    z = ret[2] if math.fabs(ret[2]) > 0.000001 else 0
    return FbxDouble3(x, y, z)

def _RollPitchYawToQuat(degrees: FbxDouble3)->FbxQuaternion:
    q = Quaternion.FQuat.Euler(Quaternion.Vector3(degrees[0], degrees[1], degrees[2]))
    ret = FbxQuaternion(q[1], q[2], q[3], q[0])
    return ret


def _RelativeDegree(parentDegree: FbxDouble3, currDegree: FbxDouble3)->FbxDouble3:
    parentQuat: FbxQuaternion = _RollPitchYawToQuat(FbxDouble3(-parentDegree[0], -parentDegree[1], -parentDegree[2]))
    parentQuat.Normalize()
    myQuat: FbxQuaternion =_RollPitchYawToQuat(currDegree)
    myQuat.Normalize()
    subQuat: FbxQuaternion = parentQuat * myQuat
    subDegree: FbxDouble3 = _QuatToRollPitchYaw(subQuat)
    return subDegree

def _BuildMatrix(node):
    q: FbxQuaternion = _RollPitchYawToQuat(node["rotation"]) if _HasAttribute(node, "rotation") else FbxQuaternion(0, 0, 0, 1)
    s: FbxDouble3 = node["scale"] if _HasAttribute(node, "scale") else FbxDouble3(1.0, 1.0, 1.0)
    m: FbxMatrix = FbxMatrix()
    pos = node["position"]
    m.SetTQS(FbxVector4(pos[0], pos[1], pos[2]), q, FbxVector4(s[0], s[1], s[2]))
    return m

def GetLocalInfo(node):
    if _HasAttribute(node, "useLocalSpace"):
        if not node["useLocalSpace"]:
            if _HasAttribute(node, "parent"):
                parentNode = node["parent"]
                m1: FbxMatrix = parentNode["worldToLocalMatrix"]
                m2: FbxMatrix = node["localToWorldMatrix"]
                m: FbxMatrix = m1 * m2
                localPos: FbxVector4 = FbxVector4()
                localQuat: FbxQuaternion = FbxQuaternion()
                localShear: FbxVector4 = FbxVector4()
                localScale: FbxVector4 = FbxVector4()
                sign = m.GetElements(localPos, localQuat, localShear, localScale)
                x = localPos[0] if math.fabs(localPos[0]) > 0.000001 else 0
                y = localPos[1] if math.fabs(localPos[1]) > 0.000001 else 0
                z = localPos[2] if math.fabs(localPos[2]) > 0.000001 else 0
                sx = localScale[0] if math.fabs(localScale[0]) > 0.000001 else 0
                sy = localScale[1] if math.fabs(localScale[1]) > 0.000001 else 0
                sz = localScale[2] if math.fabs(localScale[2]) > 0.000001 else 0
                return FbxDouble3(x, y, z), _QuatToRollPitchYaw(localQuat), FbxDouble3(sx * sign, sy * sign, sz * sign)
            else:
                return node["position"], node["rotation"], node["scale"]
    return

def _CalcWorldToLocalMatrixFromWorldSpace(node):
    if _HasAttribute(node, "useLocalSpace"):
        if not node["useLocalSpace"]:
            m = _BuildMatrix(node)
            node["localToWorldMatrix"] = m
            m = m.Inverse()
            node["worldToLocalMatrix"] = m
    return

def _CalcNodeAndChild_WorldToLocalMatrixFromWorldSpace(node):
    if _HasAttribute(node, "useLocalSpace"):
        if not node["useLocalSpace"]:
            _CalcWorldToLocalMatrixFromWorldSpace(node)
            childs = node["childs"]
            for child in childs:
                _CalcNodeAndChild_WorldToLocalMatrixFromWorldSpace(child)
    return

global cUseUnityAxis
cUseUnityAxis = True

def _CreateFbxBoneNode(fbxManager, node)->FbxNode:
    Name = node["name"]
    isRoot = len(node["childs"]) <= 0
    hasParent = _HasAttribute(node, "parent")
    skel = None
    isUseBone = node["isUseBone"]
    if isUseBone:
        skel: FbxSkeleton = FbxSkeleton.Create(fbxManager, Name)
        isRootBone = not hasParent and not isRoot
        if _HasAttribute(node, "isUseRootBone"):
            isRootBone = node["isUseRootBone"]
        if isRootBone:
            skel.SetSkeletonType(FbxSkeleton.EType.eRoot)
        else:
            skel.SetSkeletonType(FbxSkeleton.EType.eLimbNode)
    fbxNode: FbxNode = FbxNode.Create(fbxManager, Name)
    ### 设置跟UNITY一致
    fbxNode.SetTransformationInheritType(FbxTransform.EInheritType.eInheritRSrs)
    #rType = fbxNode.GetRotationOrder(FbxNode.EPivotSet.eSourcePivot)
    rType = EFbxRotationOrder(FbxEuler.EOrder.eOrderZXY.value)
    fbxNode.SetRotationOrder(FbxNode.EPivotSet.eSourcePivot, rType)
    fbxNode.SetRotationActive(True)
    if skel != None:
        fbxNode.SetNodeAttribute(skel)
    if not hasParent:
        position: FbxDouble3 = node["position"]
        if cUseUnityAxis:
            position = FbxDouble3(-position[0], position[1], position[2])
        fbxNode.LclTranslation.Set(position)
        if _HasAttribute(node, "rotation"):
            rot: FbxDouble3 = node["rotation"]
            if cUseUnityAxis:
                rot = FbxDouble3(rot[0], -rot[1], -rot[2])
            fbxNode.LclRotation.Set(rot)
        if _HasAttribute(node, "scale"):
            scale: FbxDouble3 = node["scale"]
            fbxNode.LclScaling.Set(scale)
    else:
        if node["useLocalSpace"] == True:
            position: FbxDouble3 = node["position"]
            fbxNode.LclTranslation.Set(position)
            if _HasAttribute(node, "rotation"):
                rot: FbxDouble3 = node["rotation"]
                fbxNode.LclRotation.Set(rot)
            if _HasAttribute(node, "scale"):
                scale: FbxDouble3 = node["scale"]
                fbxNode.LclScaling.Set(scale)
        else:
            '''
            parentPosition: FbxDouble3 = node["parent"]["position"]
            position: FbxDouble3 = node["position"]
            offsetPos: FbxDouble3 = FbxDouble3(position[0] - parentPosition[0], position[1] - parentPosition[1], position[2] - parentPosition[2])
            print("[offset] ", offsetPos[0], offsetPos[1], offsetPos[2])
            fbxNode.LclTranslation.Set(offsetPos)
            '''
            m1: FbxMatrix = node["parent"]["worldToLocalMatrix"]
            m2: FbxMatrix = node["localToWorldMatrix"] if _HasAttribute(node, "localToWorldMatrix") else _BuildMatrix(node)
            m: FbxMatrix = m1 * m2
            localPos: FbxVector4 = FbxVector4()
            localQuat: FbxQuaternion = FbxQuaternion()
            localShear: FbxVector4 = FbxVector4()
            localScale: FbxVector4 = FbxVector4()
            sign = m.GetElements(localPos, localQuat, localShear, localScale)
            x = localPos[0] if math.fabs(localPos[0]) > 0.000001 else 0
            y = localPos[1] if math.fabs(localPos[1]) > 0.000001 else 0
            z = localPos[2] if math.fabs(localPos[2]) > 0.000001 else 0
            if cUseUnityAxis:
                x = -x
            fbxNode.LclTranslation.Set(FbxDouble3(x, y, z))
            # print("[new offset] ", localPos[0], localPos[1], localPos[2])
            ###useRotation = False
            if _HasAttribute(node, "rotation"):
                degrees = _QuatToRollPitchYaw(localQuat)
                if cUseUnityAxis:
                    degrees = FbxDouble3(degrees[0], -degrees[1], -degrees[2])
                fbxNode.LclRotation.Set(FbxDouble3(degrees[0], degrees[1], degrees[2]))
                ##fbxNode.LclRotation.Set(FbxDouble3(0, 0, 0))
                ###useRotation = True
            if _HasAttribute(node, "scale"):
                x = localScale[0] if math.fabs(localScale[0]) > 0.000001 else 0
                y = localScale[1] if math.fabs(localScale[1]) > 0.000001 else 0
                z = localScale[2] if math.fabs(localScale[2]) > 0.000001 else 0
                fbxNode.LclScaling.Set(FbxDouble3(x * sign, y * sign, z * sign))
            ##fbxNode.SetRotationActive(True)
            ##fbxNode.SetPivotState(FbxNode.EPivotSet.eSourcePivot, FbxNode.EPivotState.ePivotReference)
            ###fbxNode.SetPreRotation(FbxNode.EPivotSet.eSourcePivot, FbxVector4(degrees[0], degrees[1], degrees[2]))

    node["FbxNode"] = fbxNode
    #fbxNode.LclTranslation.Set(node["position"])
    return fbxNode

## 创建子FBX节点
def _CreateChildFbxBoneNode(fbxManager, targetFbxNode: FbxNode, targetNode, exportBoneNum):
    for child in targetNode["childs"]:
        childFbxNode: FbxNode = _CreateFbxBoneNode(fbxManager, child)
        targetFbxNode.AddChild(childFbxNode)
        if childFbxNode.GetNodeAttributeByIndex(0) != None:
            exportBoneNum = exportBoneNum + 1
        exportBoneNum = _CreateChildFbxBoneNode(fbxManager, childFbxNode, child, exportBoneNum)
    return exportBoneNum

global _cMinWeight
_cMinWeight = 0.001

def _CreateSkin(fbxManager, scene, mesh, meshNode, vertexBoneDatas, useBoneIndexData, RootNode):
    hasUseBoneIndexData = str(type(useBoneIndexData)) != "<class 'NoneType'>"
    rootFbxNode = RootNode["FbxNode"]
    rootName = RootNode["name"]
    if hasUseBoneIndexData:
        key = str(useBoneIndexData[0])
        rootFbxNode = scene.FindNodeByName(key)
        rootName = key
    clusterRoot: FbxCluster = FbxCluster.Create(fbxManager, "Cluster_" + rootName)
    clusterRoot.SetLink(rootFbxNode)
    ##clusterRoot.SetLinkMode(FbxCluster.ELinkMode.eAdditive)
    clusterRoot.SetLinkMode(FbxCluster.ELinkMode.eNormalize)

    cluster_dict = {}
    cluster_dict[rootName] = clusterRoot
    N1 = len(vertexBoneDatas)
    VertexNum = None
    VertexBoneMap = {}
    f = open("output.log", "w")
    try:
        for i in range(0, N1, 1):
            boneWeightDatas = vertexBoneDatas[i]
            key = str(useBoneIndexData[i]) if hasUseBoneIndexData else str(i)
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
            if hasUseBoneIndexData:
                key = str(useBoneIndexData[i])
            else:
                key = str(i)
            clusterName = "Cluster_" + key
            cluster = None
            if key in cluster_dict:
                cluster = cluster_dict[key]
            else:
                cluster = FbxCluster.Create(fbxManager, clusterName)
                cluster_dict[key] = cluster
            fbxNode: FbxNode = scene.FindNodeByName(key)
            cluster.SetLink(fbxNode)
            #cluster_dict[key].SetLinkMode(FbxCluster.ELinkMode.eAdditive)
            cluster.SetLinkMode(FbxCluster.ELinkMode.eNormalize)
            N2 = len(boneWeightDatas)
            for j in range(0, N2, 1):
                if abs(boneWeightDatas[j]) >= _cMinWeight:
                    s = "boneIndex: " + str(i) + " vertexIndex: " + str(j) + " boneWeight: " + str(boneWeightDatas[j])
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

def _TransBoneNameAndChilds(boneNode):
    if boneNode == None:
        return
    if _HasAttribute(boneNode, "realName"):
        boneRealName = boneNode["realName"]
        fbxBone: FbxNode = boneNode["FbxNode"]
        fbxBone.SetName(boneRealName)
    for childNode in boneNode["childs"]:
        _TransBoneNameAndChilds(childNode)
    return

def _CreateNode(name, position: FbxDouble3, rotation: FbxDouble3, scale: FbxDouble3, useLocalSpace: bool):
    ret = {
        "position": FbxDouble3(position[0], position[1], position[2]),  # 位置
        "childs": [],
        "name": str(name),  ## 骨骼名称
        "useLocalSpace": useLocalSpace,  # 坐标系是否是局部坐标系
        "realName": str(name),
        "rotation": FbxDouble3(rotation[0], rotation[1], rotation[2]) if str(type(rotation)) != "<class 'NoneType'>" else None,  # 角度制(坐标系看useLocalSpace)
        "scale": FbxDouble3(scale[0], scale[1],
                            scale[2]) if str(type(scale)) != "<class 'NoneType'>" else None,  # 缩放(坐标系看useLocalSpace)
    }
    return ret

def _RemoveChildNode(childNode: dict):
    if not _HasAttribute(childNode, "parent"):
        return
    parentNode = childNode["parent"]
    parentNode["childs"].remove(childNode)
    childNode.pop("parent")
    return

def _AddChildNode(parentNode, childNode):
    if childNode in parentNode["childs"]:
        return
    _RemoveChildNode(childNode)
    parentNode["childs"].append(childNode)
    childNode["parent"] = parentNode
    return

##### 生成骨骼拓扑结构
def _BuildBoneMap(fbxManager, scene, bonePosDatas, boneRotDatas, boneScaleDateas, boneLinkDatas, boneNamesData, useBoneIndexData, useLocalSpace):
    ## 骨骼KEY（字符串）和位置建立关系
    boneNum = len(bonePosDatas)
    if boneNum <= 0:
        return
    boneIndexIsUseBone = {}
    hasUseBoneIndexData = str(type(useBoneIndexData)) != "<class 'NoneType'>"
    useRootBoneIndex = None
    if hasUseBoneIndexData:
        ##useBoneIndexData = np.sort(useBoneIndexData) ## 不要排序
        for i in range(len(useBoneIndexData)):
            idx = useBoneIndexData[i]
            boneIndexIsUseBone[idx] = True
            if i == 0:
                useRootBoneIndex = idx
    exportBoneMap = {}  ## 骨骼名对应位置
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
        boneRealName = None
        hasBoneRealName = str(type(boneNamesData)) != "<class 'NoneType'>"
        if hasBoneRealName:
            boneRealName = boneNamesData[i]
        key = str(i)
        exportBoneMap[key] = {
            "position": FbxDouble3(bonePos[0], bonePos[1], bonePos[2]),  # 位置
            "childs": [],
            "name": str(i),  ## 骨骼名称
            "useLocalSpace": useLocalSpace,  # 坐标系是否是局部坐标系
            "realName": boneRealName if hasBoneRealName else None,
            "rotation": FbxDouble3(boneRot[0], boneRot[1], boneRot[2]) if hasBoneRot else None,
            # 角度制(坐标系看useLocalSpace)
            "scale": FbxDouble3(boneScale[0], boneScale[1], boneScale[2]) if hasBoneScale else None,
            # 缩放(坐标系看useLocalSpace)
            "isUseBone": (i in boneIndexIsUseBone) if hasUseBoneIndexData else True, ## 是否是使用的骨骼
            "isUseRootBone": i == useRootBoneIndex if useRootBoneIndex != None else None,
        }
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
        if _HasAttribute(value, "parent"):
            removeList.append(key)
    for key in removeList:
        exportBoneMap.pop(key, None)
    if not useLocalSpace:
        ## 如果世界坐标系中，获得worldToLocalMatrix
        print("generate worldToLocalMatrix...")
        for key, value in exportBoneMap.items():
            _CalcNodeAndChild_WorldToLocalMatrixFromWorldSpace(value)
    ## 生成FbxSkeleton
    exportBoneNum = 0
    RootNode = None
    for key, value in exportBoneMap.items():
        RootNode = value
        if fbxManager != None and scene != None:
            fbxRootNode: FbxNode = _CreateFbxBoneNode(fbxManager, value)
            if fbxRootNode.GetNodeAttributeByIndex(0) != None:
                exportBoneNum = exportBoneNum + 1
            exportBoneNum = _CreateChildFbxBoneNode(fbxManager, fbxRootNode, value, exportBoneNum)
            scene.GetRootNode().GetChild(0).AddChild(fbxRootNode)
    print("[export] boneNum: %d" % exportBoneNum)
    return exportBoneMap, RootNode, boneIndexIsUseBone

def AddSkinnedDataToMesh(fbxManager, scene, mesh, meshNode, vertexBoneDatas, bonePosDatas, boneRotDatas,
                         boneScaleDateas, boneLinkDatas, boneNamesData, useBoneIndexData, useLocalSpace):
    exportBoneMap, RootNode, useRootBoneIndex = _BuildBoneMap(fbxManager, scene, bonePosDatas, boneRotDatas, boneScaleDateas, boneLinkDatas, boneNamesData, useBoneIndexData, useLocalSpace)
    ## 顶点蒙皮
    _CreateSkin(fbxManager, scene, mesh, meshNode, vertexBoneDatas, useBoneIndexData, RootNode)
    ## 更换骨骼节点名(执行放最后)
    if RootNode != None:
        _TransBoneNameAndChilds(RootNode)
    return

global bUseSceneImport
bUseSceneImport = True

## obj模型 顶点BoneWeight 骨骼位置 骨骼父子关系 导出文件
def BuildFBXData(objFileName, vertBoneDataFileName, boneLocDataFileName, boneRotDataFileName, boneScaleDataFileName,
                 skeleteLinkFileName, boneNamesFileName, useBoneIndexFileName, useLocalSpace = False, outFileName = "out.fbx"):
    if bUseSceneImport:
        manager, scene = FbxCommon.InitializeSdkObjects()

        globalSetting: FbxGlobalSettings = scene.GetGlobalSettings()

        ######################### 将坐标系设置成和UNITY一致的情况 ###########################################################
        '''
        oldSystem: FbxAxisSystem = globalSetting.GetAxisSystem()
        oldUpVector, oldUpSign = oldSystem.GetUpVector()
        oldFrontVector, oldFrontSign = oldSystem.GetFrontVector()
        axisSystem: FbxAxisSystem = FbxAxisSystem(oldUpVector,
                                                  oldFrontVector,
                                                  FbxAxisSystem.ECoordSystem.eLeftHanded)
        globalSetting.SetOriginalUpAxis(axisSystem)
        globalSetting.SetAxisSystem(axisSystem)
        
        axisSystem = globalSetting.GetAxisSystem()
        print("坐标系左手坐标系还是有右手: ", axisSystem.GetCoorSystem())
        print("UpVector: ", axisSystem.GetUpVector())
        '''
        ###############################################################################################################
        globalSetting.SetOriginalSystemUnit(FbxSystemUnit.m)
        globalSetting.SetSystemUnit(FbxSystemUnit.m)

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
        ## 节点关联信息
        boneLinkDatas = np.load(skeleteLinkFileName)
        ## 节点位置信息
        boneLocDatas = np.load(boneLocDataFileName)
        ## 节点旋转信息
        boneRotDatas = None
        if boneRotDataFileName != None:
            boneRotDatas = np.load(boneRotDataFileName)
        ## 节点缩放信息
        boneScaleDatas = None
        if boneScaleDataFileName != None:
            boneScaleDatas = np.load(boneScaleDataFileName)
        ## 节点名称
        boneNamesData = None
        if boneNamesFileName != None:
            boneNamesData = np.load(boneNamesFileName)
        ## useBone
        useBoneIndexData = None
        if useBoneIndexFileName != None:
            useBoneIndexData = np.load(useBoneIndexFileName)
        # 导入骨骼和蒙皮信息，让mesh变skinnedMesh
        # AddSkinnedDataToMesh(fbxManager, scene, mesh, meshNode, vertexBoneDatas, bonePosDatas, boneRotDatas, boneScaleDateas, boneLinkDatas, boneNamesData, useLocalSpace)
        AddSkinnedDataToMesh(manager, scene, mesh, meshNode, vertexBoneDatas, boneLocDatas, boneRotDatas,
                            boneScaleDatas, boneLinkDatas, boneNamesData, useBoneIndexData, useLocalSpace)
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
        ## 骨骼名称
        boneNamesData = None
        if boneNamesFileName != None:
            boneNamesData = np.load(boneNamesFileName)
        useBoneIndexData = None
        if useBoneIndexFileName != None:
            useBoneIndexData = np.load(useBoneIndexFileName)
        ## 初始化FBX环境
        manager, scene = FbxCommon.InitializeSdkObjects()
        # 创建Mesh
        mesh, meshNode = CreateMesh(scene, "Character", vertexs, normals, texcoords, faces)
        # 导入骨骼和蒙皮信息，让mesh变skinnedMesh
        AddSkinnedDataToMesh(manager, scene, mesh, meshNode, vertexBoneDatas, boneLocDatas, boneRotDatas,
                             boneScaleDatas, boneLinkDatas, boneNamesData, useBoneIndexData, useLocalSpace)
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
    ## 骨骼名称
    print("[Generate] Convert boneName to names...")
    Generate_Json_ToNPY(dir, name, "names")
    ## 使用的骨骼索引
    print("[Generate] Convert boneName to use bone indexs...")
    Generate_Json_ToNPY(dir, name, "boneIndexs")
    return

# 使用obj文件和NPY文件生成FBX
def Generate_ObjAndNPY_ToFBX(dir, name, useLocalSpace):
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
    boneNamesFileName = "%s/%s_names.npy" % (dir, name)
    boneNamesFileName = os.path.abspath(boneNamesFileName)
    if not os.path.exists(boneNamesFileName):
        boneNamesFileName = None
    useBoneIndexFileName = "%s/%s_boneIndexs.npy" % (dir, name)
    useBoneIndexFileName = os.path.abspath(useBoneIndexFileName)
    if not os.path.exists(useBoneIndexFileName):
        useBoneIndexFileName = None
    ## BuildFBXData(objFileName, vertBoneDataFileName, boneLocDataFileName, boneRotDataFileName, boneScaleDataFileName, skeleteLinkFileName, boneNamesFileName, useLocalSpace, outFileName = "out.fbx")
    BuildFBXData(objFileName, vertexBoneFileName, boneLocFileName, boneRotFileName, boneScaleFileName,
                 boneLinkeFileName, boneNamesFileName, useBoneIndexFileName, useLocalSpace)
    return

def _BoneAndChild_To_Map(bone, boneMap):
    index = int(bone["name"])
    boneMap[index] = bone
    childs = bone["childs"]
    for child in childs:
        _BoneAndChild_To_Map(child, boneMap)
    return

## 骨骼局部位置，旋转，缩放。写入文件
def Write_World_Convert_RelativeBoneDataToJson(dir, name):
    '''
    objFileName = "%s/%s.obj" % (dir, name)
    objFileName = os.path.abspath(objFileName)
    if not os.path.exists(objFileName):
        return
    '''
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
    boneNamesFileName = "%s/%s_names.npy" % (dir, name)
    boneNamesFileName = os.path.abspath(boneNamesFileName)
    if not os.path.exists(boneNamesFileName):
        boneNamesFileName = None

    ############# 读取数据
    ## vertex骨骼信息
    vertexBoneDatas = np.load(vertexBoneFileName)
    ## 骨骼关联信息
    boneLinkDatas = np.load(boneLinkeFileName)
    ## 骨骼位置信息
    boneLocDatas = np.load(boneLocFileName)
    ## 骨骼旋转信息
    boneRotDatas = None
    if boneRotFileName != None:
        boneRotDatas = np.load(boneRotFileName)
    ## 骨骼缩放信息
    boneScaleDatas = None
    if boneScaleFileName != None:
        boneScaleDatas = np.load(boneScaleFileName)
    ## 骨骼名称
    boneNamesData = None
    if boneNamesFileName != None:
        boneNamesData = np.load(boneNamesFileName)
    ## 拓扑结构
    exportBoneMap, skelRootNode, _ = _BuildBoneMap(None, None, boneLocDatas, boneRotDatas, boneScaleDatas, boneLinkDatas, boneNamesData, None,
                  False)

    boneNum = len(boneLocDatas)
    boneMap = {}
    ## 转化成boneList
    for _, value in exportBoneMap.items():
        _BoneAndChild_To_Map(value, boneMap)
    boneList = []
    for idx in range(0, boneNum):
        boneList.append(boneMap[idx])

    exportBoneList = []
    for bone in boneList:
        localPos, localRot, localScale = GetLocalInfo(bone)
        d = {
            "name": bone["realName"] if _HasAttribute(bone, "realName") else bone["name"],
            "index": bone["name"],
            "parent": bone["parent"]["name"] if _HasAttribute(bone, "parent") else -1,
            "localPos": [localPos[0], localPos[1], localPos[2]],
            "localRot": [localRot[0], localRot[1], localRot[2]],
            "localScale": [localScale[0], localScale[1], localScale[2]],
        }
        exportBoneList.append(d)

    str = json.dumps(exportBoneList, ensure_ascii=True, indent=4)
    outFileName = "%s/%s_local.json" % (dir, name)
    f = open(outFileName, "w")
    try:
        f.write(str)
    finally:
        f.close()
    return

def Test():
    #a = _CreateNode("a", FbxDouble3(-4.458028, -10.86612, -23.77408), FbxDouble3(-89.98, 0, 0), FbxDouble3(1, 1, 1), False)
    b = _CreateNode("b", FbxDouble3(0, 0, 0), FbxDouble3(-90, 0, 180), FbxDouble3(1, 1, 1), False)
    c = _CreateNode("c", FbxDouble3(100, 0, 0), FbxDouble3(90, 0, 0), FbxDouble3(1, 1, 1), False)
    #_AddChildNode(a, b)
    _AddChildNode(b, c)
    _CalcNodeAndChild_WorldToLocalMatrixFromWorldSpace(b)
    localPos, localRot, localScale = GetLocalInfo(c)
    print("localPos:", localPos[0], localPos[1], localPos[2])
    print("localRot:", localRot[0], localRot[1], localRot[2])
    print("local Scale", localScale[0], localScale[1], localScale[2])
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
            Generate_ObjAndNPY_ToFBX(dir, name, False)
            return
        elif argv[1] == "out-local":
            dir = str(argv[2])
            name = str(argv[3])
            Write_World_Convert_RelativeBoneDataToJson(dir, name)
        return
    '''
    parenteRot = FbxDouble3(45, 0, 0)
    rot = FbxDouble3(45, 45, 0)
    subRot = _RelativeDegree(parenteRot, rot)
    print(subRot[0], subRot[1], subRot[2])
    return
    '''
    #Write_World_Convert_RelativeBoneDataToJson("./example_json", "HuMan")
    #return
    ##print(type(None))
    #BuildFBXData(GetTestObjFilePath(), GetTestVertexBoneDataPath(), GetTestBoneDataPath(), None, None,
    #            GetTestSkeleteLinkPath(), None, None)
    Generate_ObjAndNPY_ToFBX("./example_json", "HuMan", False)
    #Generate_JsonToNPY("./example_json", "hero_kof_kyo_body_0002")
    return

##################################### 调用入口 ###################################
if __name__ == '__main__':
    Main()
#################################################################################