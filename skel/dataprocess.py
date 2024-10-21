import os
import shutil
import io
from tqdm import tqdm

data_path = '/mnt/workspace/project/data/vrm/test_3dgs_demo2/'
save_path = './results/rig_info_gt/'

os.makedirs(save_path, exist_ok=True)

# 遍历train_subset文件夹中的所有文件
for con_filename in tqdm(os.listdir(data_path)):
    # 检查文件名是否在我们的集合中
    if '_connectivity' in con_filename:
        name = con_filename.split('_')[0]
        
#         if name != "936557262981337495":
#             continue
        # if os.path.exists(os.path.join(save_path, f'{name}.txt')):
        #     continue
        
        filename = con_filename.replace('_connectivity', '_j')
        # print(filename)
        skin_filename = con_filename.replace('_connectivity', '_skin')
        # print(skin_filename)
        # 读取filename和confilename文件
        with open(os.path.join(data_path, filename), 'r') as f:
            lines_filename = f.readlines()
            # print(lines_filename)
        with open(os.path.join(data_path, con_filename), 'r') as f:
            lines_confilename = f.readlines()
            
        with open(os.path.join(data_path, skin_filename), 'r') as f:
            lines_skin = f.readlines()
    
        # 对于每一行，读取数据并转换为需要的格式
        skin_info = ''
        hie_info = ''
        rig_info = ''
        rig_idx ={}
        i=0
        for line_filename, line_confilename in zip(lines_filename, lines_confilename):
            joint_name = line_confilename.split()[0]
            coordinates = line_filename.split()
            # print(coordinates)
            rig_info += f'joints {joint_name} {" ".join(coordinates)}\n'
            rig_idx[i] = joint_name
            i+=1
            joint_father_name = line_confilename.split()[1]
            if joint_father_name != 'None':
                hie_info += f'hier {joint_father_name} {joint_name}\n'
                
        # print("there are ", i, "joints in the rig_info file")
        # print(rig_idx)
        # 添加root
        root_joint = lines_confilename[0].split()[0]
        rig_info += f'root {root_joint}\n'
        
        # 处理skin信息
        for line_idx,line_skin in enumerate(lines_skin):
            weights = line_skin.split(" ")
            # print(weights)
            skin_info += f'skin {line_idx}'
            for idx, weight in enumerate(weights):
                if float(weight) != 0:
                    skin_info += f' {rig_idx[idx]} {weight}'

            skin_info += '\n'
            
        rig_info += skin_info
        rig_info += hie_info
        # 将转换后的数据写入新的rig_info文件夹中的文件
        with open(os.path.join(save_path, f'{name}.txt'), 'w') as f:
            f.write(rig_info)

            
dir_path = save_path
# 使用 os.listdir 函数获取文件夹中的文件列表
files = os.listdir(dir_path)
for file_name in files:
    file_path = os.path.join(dir_path, file_name)
    # 读取文件内容，去除空白行
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        lines = [line for line in lines if line.strip() != '']
        # 将处理后的内容写回文件
        with open(file_path, 'w') as file:
            file.writelines(lines)
    except:
        print(file_name)
        continue