import numpy as np
from objloader import Obj
import FbxCommon

def BuildFBXData(objFileName):
    model = Obj.open(objFileName)
    ## 位置数据
    vertexs = np.array(model.vertices)
    ## 法线
    normals = np.array(model.normals)
    ## 纹理坐标
    texcoords = np.array(model.faces)
    ## 三角面索引列表
    faces = np.array(model.faces)
    return

def Main():
    return

##################################### 调用入口 ###################################
if __name__ == '__main__':
    Main()
#################################################################################