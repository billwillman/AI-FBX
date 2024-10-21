【安装步骤】
1.Setup目录安装：python-3.10.11-amd64.exe
2.设置环境变量Path: 
  示例：
  C:\Users\XXXX\AppData\Local\Programs\Python\Python310
  C:\Users\XXXX\AppData\Local\Programs\Python\Python310\Scripts
3.安装Python依赖库：
  PyInstall.bat

【测试环境是否正常】
双击：AI-FBX\Tools\PyFbxCombine\PyFbxCombine\PyFBXCombine.bat
生成：out.fbx 说明环境正常。

【待办1】
完成Unity的SkinnedMesh流程部分，子步骤拆分：
1.完成初步流程 Vertex Data的BoneIndex, BoneWeight, BindPoseMatrix。
2.完成初步流程 骨架信息Bone的FBX写入。
3.最终：让FBX导入Unity可识别为SkinnedMesh

【待办2】
1. 写入生成动画到FBX部分
2. 最终导入Unity动画可识别，骨骼动画播放正确，顶点蒙皮表现正常。

【待办3】
代码结构调整，需要思考不同格式下输入数据FBX生成正确，例如：
1. 多Material的SubMesh情况。
2. 多UV，或者无UV以及normal，切线，副法线有无情况。

