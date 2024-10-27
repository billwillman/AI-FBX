import os
import numpy as np
from objloader import Obj
from fbx import *
import FbxCommon
from operator import index
from test.test_importlib.import_.test_fromlist import ReturnValue


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
    return mesh, currentNodes

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
        fbxNode.LclTranslation.Set(FbxDouble3(0, 0, 0))
    else:
        parentPosition: FbxDouble3 = node["parent"]["position"]
        position: FbxDouble3 = node["position"]
        offsetPos: FbxDouble3 = FbxDouble3(position[0] - parentPosition[0], position[1] - parentPosition[1], position[2] - parentPosition[2])
        fbxNode.LclTranslation.Set(offsetPos)
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

def _CreateSkin(fbxManager, scene, mesh, meshNode, vertexBoneDatas, skelRootNode):
    rootFbxNode = skelRootNode["FbxNode"]
    clusterRoot: FbxCluster = FbxCluster.Create(fbxManager, "Cluster_" + skelRootNode["name"])
    clusterRoot.SetLink(rootFbxNode)
    clusterRoot.SetLinkMode(FbxCluster.ELinkMode.eAdditive)

    cluster_dict = {}
    for i in range(0, len(vertexBoneDatas), 1):
        boneWeightDatas = vertexBoneDatas[i]
        key = str(i)
        cluster_dict[key]: FbxCluster = FbxCluster.Create(fbxManager, "Cluster_" + key)
        fbxNode: FbxNode = scene.FindNodeByName(key)
        cluster_dict[key].SetLink(fbxNode)
        cluster_dict[key].SetLinkMode(FbxCluster.ELinkMode.eAdditive)
        for j in range(0, len(boneWeightDatas), 1):
            if abs(boneWeightDatas[j]) >= 0.000001:
                cluster_dict[key].AddControlPointIndex(j, boneWeightDatas[j])

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

def AddSkinnedDataToMesh(fbxManager, scene, mesh, meshNode, vertexBoneDatas, boneDatas, boneLinkDatas):
    ## 骨骼KEY（字符串）和位置建立关系
    boneNum = len(boneDatas)
    if boneNum <= 0:
        return
    exportBoneMap = {} ## 骨骼名对应位置
    for i in range(0, boneNum, 1):
        bonePos = boneDatas[i]
        exportBoneMap[str(i)] = {
            "position": FbxDouble3(bonePos[0], bonePos[1], bonePos[2]),
            "childs": [],
            "name": str(i), ## 骨骼名称
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

def BuildFBXData(objFileName, vertBoneDataFileName, boneDataFileName, skeleteLinkFileName, outFileName = "out.fbx"):
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
        ## 骨骼信息
        boneDatas = np.load(boneDataFileName)
        # 导入骨骼和蒙皮信息，让mesh变skinnedMesh
        AddSkinnedDataToMesh(manager, scene, mesh, meshNode, vertexBoneDatas, boneDatas, boneLinkDatas)
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
        boneDatas = np.load(boneDataFileName)
        ## 初始化FBX环境
        manager, scene = FbxCommon.InitializeSdkObjects()
        # 创建Mesh
        mesh, meshNode = CreateMesh(scene, "Character", vertexs, normals, texcoords, faces)
        # 导入骨骼和蒙皮信息，让mesh变skinnedMesh
        AddSkinnedDataToMesh(manager, scene, mesh, meshNode, vertexBoneDatas, boneDatas, boneLinkDatas)
    ## 导出
    FbxCommon.SaveScene(manager, scene, outFileName)
    return

def Main():
    BuildFBXData(GetTestObjFilePath(), GetTestVertexBoneDataPath(), GetTestBoneDataPath(), GetTestSkeleteLinkPath())
    return

##################################### 调用入口 ###################################
if __name__ == '__main__':
    Main()
#################################################################################