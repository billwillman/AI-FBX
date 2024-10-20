import os
import numpy as np
from objloader import Obj
from fbx import *
import FbxCommon

def GetAbsoluteRootPath():
    result = os.path.dirname(os.path.realpath(__file__))
    return result

def GetTestObjFilePath():
    ret = GetAbsoluteRootPath() + "/../../../res2/save_obj/xudong_mesh.obj"
    ret = os.path.abspath(ret)
    return ret

def GetTestVertexBoneDataPath():
    ret = GetAbsoluteRootPath() + "/../../../res2/save_obj/xudong_mesh.npy"
    ret = os.path.abspath(ret)
    return ret

def GetTestSkeletePath():
    ret = GetAbsoluteRootPath() + "/../../../res2/save_obj/mesh_parents.npy"
    ret = os.path.abspath(ret)
    return ret

def CreateMesh(scene, meshName, vertexs, normals, texcoords, faces):
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
    layerIndex = 0
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
        mesh.CreateLayer()
        layer: FbxLayer = mesh.GetLayer(layerIndex)
        layer.SetNormals(normalElement)
        layerIndex += 1
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
        mesh.CreateLayer()
        layer: FbxLayer = mesh.GetLayer(layerIndex)
        layer.SetUVs(uvElement)
        layerIndex += 1
        faceSubIdx += 1

    mesh.BuildMeshEdgeArray() # 生成边界数组
    currentNode.AddNodeAttribute(mesh)

    rootNode.AddChild(currentNode)
    return

def BuildFBXData(objFileName, vertBoneDataFileName, skeleteFileName, outFileName = "out.fbx"):
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
    ## 骨骼信息
    boneDatas = np.load(skeleteFileName)
    ## 初始化FBX环境
    manager, scene = FbxCommon.InitializeSdkObjects()
    # 创建Mesh
    CreateMesh(scene, "Character", vertexs, normals, texcoords, faces)
    ## 导出
    FbxCommon.SaveScene(manager, scene, outFileName)
    return

def Main():
    BuildFBXData(GetTestObjFilePath(), GetTestVertexBoneDataPath(), GetTestSkeletePath())
    return

##################################### 调用入口 ###################################
if __name__ == '__main__':
    Main()
#################################################################################