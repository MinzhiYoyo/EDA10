import importlib.util
import warnings
import os
import sys 
import random
import tempfile
from pathlib import Path

def dynamic_import(group_id):
    """
    动态导入指定参赛队伍的 my_solution 模块
    """
    group_info = group_code_info[group_id]
    code_path = group_info['code_path']
    module_name = group_info['module_name']
    
    # 构建模块的完整路径
    # 将模块所在目录添加到 sys.path
    sys.path.append(code_path)
    os.chdir(code_path)
    module_path = os.path.join(code_path, f"{module_name}.py")
    
    # 动态导入模块
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module



def get_image(image_path):
    with open(image_path,'rb') as img_file:
        case_image = img_file.read()
    return case_image


def run_tests(solution,group_id):
    load_dir = r'/home/public/public/images'
    save_dir = f'{os.getcwd()}/generate_new'
    save_dir_ct = f'{os.getcwd()}/generate_ct'
    if not os.path.exists(save_dir_ct):
        os.makedirs(save_dir_ct)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    import tqdm 
    import time 
    
    files = os.listdir(load_dir)
    random.shuffle(files)  
    
    for file in tqdm.tqdm(files):
        print('-----------------------------------------Begin File:', file)
        
        file_name = os.path.join(load_dir, file)
        with tempfile.NamedTemporaryFile(delete=True, suffix=".png") as tf:
            img = Path(file_name).read_bytes()
            Path(tf.name).write_bytes(img)
            
            st=time.time()
            result = solution(tf.name)
            ct=round(time.time()-st,3)
        
        save_name = file.replace('.png', '.txt')
        print(os.path.join(save_dir, save_name))
        with open(os.path.join(save_dir, save_name), 'w') as f:
            f.write(str(result))
        save_name=file.replace('.png', f'_{ct}.txt')
        with open(os.path.join(save_dir_ct, save_name), 'w') as f:
            f.write(str(result))
        print('-----------------------------------------File completed:', file)

    print(f"******************************************{group_id} finished!!******************************************")

if __name__ == '__main__':
    # 忽略警告信息
    warnings.filterwarnings("ignore", category=FutureWarning)
    ##说明：1. 修改group_code_info的信息，参赛队伍的信息,参赛队的id，code_path:项目代码地址，module_name：模块地址
    ##      2. 结果会在当前文件夹
    group_code_info = {
        "edatest": {"code_path": os.getcwd(), "module_name": "my_solution"},
    }


    # 遍历所有参赛队伍，导入并运行测试
    for group_id in group_code_info:
        # try:
        # 动态导入模块
        solution_module = dynamic_import(group_id)
        
        # 获取 solution 函数
        solution = getattr(solution_module, 'solution', None)
        if solution is None:
            raise AttributeError(f"Module {group_id} does not have a 'solution' function.")
        # 运行测试
        run_tests(solution,group_id)
        # except Exception as e:
        #     print(f"Error processing group {group_id}: {e}")