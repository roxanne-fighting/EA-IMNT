from tkinter import SE
import tensorflow as tf
from include.Config import Config
from include.Model import build, training
from include.Test import get_hits
from include.Load import *
import sys
import warnings
warnings.filterwarnings("ignore")

'''
Follow the code style of GCN-Align:
https://github.com/1049451037/GCN-Align
'''

seed = 12306
np.random.seed(seed)
tf.set_random_seed(seed)

if __name__ == '__main__':
    # language seed name_lose raw_method
    language = sys.argv[1]#'fr_en' # zh_en | ja_en | fr_en
    seed = int(sys.argv[2])#3  # 30% of seeds
    name_lose = int(sys.argv[3]) # 5 %5
    raw_method = int(sys.argv[4])
    print("Is raw_method:",bool(raw_method))
    e1 = 'data/' + language + '/ent_ids_1'
    e2 = 'data/' + language + '/ent_ids_2'
    ill = 'data/' + language + '/ref_ent_ids'
    kg1 = 'data/' + language + '/triples_1'
    kg2 = 'data/' + language + '/triples_2'
    epochs = 600
    dim = 300
    act_func = tf.nn.relu
    alpha = 0.1
    beta = 0.3
    gamma = 1.0  # margin based loss
    k = 125  # number of negative samples for each positive one
   
    # load element in e1 and e2 我们只读取id 对于第二列的网站，or name 我们忽略它
    # 注意这里只计算了实体的数量
    set_e1 = set(loadfile(e1, 1))
    set_e2 = set(loadfile(e2, 1))
    e = len(set_e1 | set_e2 )
    print('e1:{},e2{} number of all entity:{}'.format(len(set_e1),len(set_e2),e))
    # 实体连接 ILL 是 n x 2 的列表 表示 对齐的实体
    ILL = loadfile(ill, 2)
    illL = len(ILL)
    # 随机打乱顺序
    np.random.shuffle(ILL)
    # 取seed%数据作为训练集
    train = np.array(ILL[:illL // 10 * seed])
    # 之后的作为测试集
    test = ILL[illL // 10 * seed:]

    # 知识图谱(关系三元组) 它是一个 n x 3的列表 每个元素代表 实体1 关系 实体2
    KG1 = loadfile(kg1, 3)
    KG2 = loadfile(kg2, 3)

    output_layer, loss = build(
        dim, act_func, alpha, beta, gamma, k, language[0:2], e, train,name_lose,raw_method, KG1 + KG2)
    vec, J = training(output_layer, loss, 0.001,
                      epochs, train, e, k, test)
    print('loss:', J)
    print('Result:')
    get_hits(vec, test)
