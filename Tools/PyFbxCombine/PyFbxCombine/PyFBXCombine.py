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

    mesh = FbxMesh.Create(scene, meshName)
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
    ## 创建Character
    #charIndex = scene.CreateCharacter("Character")
    #char = scene.GetCharacter(charIndex)
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