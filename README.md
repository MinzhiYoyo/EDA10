# 除赛题方提供的代码之外，需要用到的程序源文件

```
submission/
├── EDADataSet/
│   └── EDADataSet.py
├── EDAModel/
│   └── NetlistModel.py
├── EDAPublic/
│   └── EDACV.py
├── Graph/
│   ├── EDADrawGraph.py
│   └── EDANode.py
├── bjt_detect.py
├── mos_detect.py
├── cur_detect.py
├── diode_detect.py
├── predict.py
├── my_solution.py
├── best.pt
├── predict_function.pkl
├── config.json
└── requirements.txt
```

# 安装依赖库

```shell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

# 运行程序

```shell
python get_raw_result.py
python get_final_result.py
```

# 附：所用到的第三方库及其官方下载地址

1. numpy~=1.26.4: https://www.numpy.org/ 
2. opencv-python~=4.10.0.84: https://www.piwheels.org/project/opencv-python/ 
3. pillow~=10.4.0: https://python-pillow.org/
4. matplotlib~=3.9.2: https://matplotlib.org/
5. ultralytics~=8.3.29: https://www.ultralytics.com/
6. scipy~=1.13.1: https://scipy.org/
7. scikit-learn~=1.5.2: https://scikit-learn.org/
8. networkx~=3.2.1: https://networkx.org/
9. torch~=2.5.1: https://pytorch.org/
10. tqdm~=4.66.6: https://tqdm.github.io/