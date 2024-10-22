bodai_mesh_joints.npy: 骨架的关键点，shape是55x3
bodai_mesh_parents.npy： 骨架拓扑结构的定义，shape是55x1，e.g.，索引i的元素表示第i个joint对应的父节点的index
bodai_mesh.npy：blending weight，shape是55xN，N表示mesh的顶点数，55表示每个joint对应的蒙皮权重
