import math
from .Init import *
from include.Test import get_hits
import scipy
import json
import scipy.spatial
import numpy as np
def rfunc(KG, e):
    # 记录关系的head
    head = {}
    # 记录关系的tail
    tail = {}
    # 记录关系的数量
    cnt = {}
    for tri in KG:
        if tri[1] not in cnt:
            cnt[tri[1]] = 1
            head[tri[1]] = set([tri[0]])
            tail[tri[1]] = set([tri[2]])
        else:
            cnt[tri[1]] += 1
            head[tri[1]].add(tri[0])
            tail[tri[1]].add(tri[2])
    r_num = len(head)
    head_r = np.zeros((e, r_num))
    # 这里是bug?
    tail_r = np.zeros((e, r_num))
    r_mat_ind = []
    r_mat_val = []
    for tri in KG:
        head_r[tri[0]][tri[1]] = 1
        tail_r[tri[2]][tri[1]] = 1
        r_mat_ind.append([tri[0], tri[2]])
        r_mat_val.append(tri[1])
    r_mat = tf.SparseTensor(
        indices=r_mat_ind, values=r_mat_val, dense_shape=[e, e])

    return head, tail, head_r, tail_r, r_mat


def get_mat(e, KG):
    # set list
    du = [{e_id} for e_id in range(e)]
    # 记录实体通过关系连接的所有相邻实体
    for tri in KG:
        if tri[0] != tri[2]:
            du[tri[0]].add(tri[2])
            du[tri[2]].add(tri[0])
    # 连接数量 图论中称为度？
    du = [len(d) for d in du]
    M = {}
    # 邻接矩阵
    for tri in KG:
        if tri[0] == tri[2]:
            continue
        if (tri[0], tri[2]) not in M:
            M[(tri[0], tri[2])] = 1
        else:
            pass
        if (tri[2], tri[0]) not in M:
            M[(tri[2], tri[0])] = 1
        else:
            pass

    for i in range(e):
        M[(i, i)] = 1
    return M, du


# get a sparse tensor based on relational triples
def get_sparse_tensor(e, KG):
    print('getting a sparse tensor...')
    # 邻接矩阵及其度
    M, du = get_mat(e, KG)
    ind = []
    val = []
    M_arr = np.zeros((e, e))
    for fir, sec in M:
        ind.append((sec, fir))
        # 这是为什么？
        val.append(M[(fir, sec)] / math.sqrt(du[fir]) / math.sqrt(du[sec]))
        M_arr[fir][sec] = 1.0
    M = tf.SparseTensor(indices=ind, values=val, dense_shape=[e, e])

    return M, M_arr


# add a layer
def add_diag_layer(inlayer, dimension, M, act_func, dropout=0.0, init=ones):
    inlayer = tf.nn.dropout(inlayer, 1 - dropout)
    print('adding a diag layer...')
    w0 = init([1, dimension])
    tosum = tf.sparse_tensor_dense_matmul(M, tf.multiply(inlayer, w0))
    if act_func is None:
        return tosum
    else:
        return act_func(tosum)


def add_full_layer(inlayer, dimension_in, dimension_out, M, act_func, dropout=0.0, init=glorot):
    inlayer = tf.nn.dropout(inlayer, 1 - dropout)
    print('adding a full layer...')
    w0 = init([dimension_in, dimension_out])
    tosum = tf.sparse_tensor_dense_matmul(M, tf.matmul(inlayer, w0))
    if act_func is None:
        return tosum
    else:
        return act_func(tosum)


def add_sparse_att_layer(inlayer, dual_layer, r_mat, act_func, e):
    dual_transform = tf.reshape(tf.layers.conv1d(
        tf.expand_dims(dual_layer, 0), 1, 1), (-1, 1))
    logits = tf.reshape(tf.nn.embedding_lookup(
        dual_transform, r_mat.values), [-1])
    print('adding sparse attention layer...')
    lrelu = tf.SparseTensor(indices=r_mat.indices,
                            values=tf.nn.leaky_relu(logits),
                            dense_shape=(r_mat.dense_shape))
    coefs = tf.sparse_softmax(lrelu)
    # eq (7)
    vals = tf.sparse_tensor_dense_matmul(coefs, inlayer)
    # eq (6)
    if act_func is None:
        return vals
    else:
        return act_func(vals)


def add_dual_att_layer(inlayer, inlayer2, adj_mat, act_func, hid_dim):
    in_fts = tf.layers.conv1d(tf.expand_dims(inlayer2, 0), hid_dim, 1)
    f_1 = tf.reshape(tf.layers.conv1d(in_fts, 1, 1), (-1, 1))
    f_2 = tf.reshape(tf.layers.conv1d(in_fts, 1, 1), (-1, 1))
    logits = f_1 + tf.transpose(f_2)
    print('adding dual attention layer...')
    adj_tensor = tf.constant(adj_mat, dtype=tf.float32)
    bias_mat = -1e9 * (1.0 - (adj_mat > 0))
    logits = tf.multiply(adj_tensor, logits)
    coefs = tf.nn.softmax(tf.nn.leaky_relu(logits) + bias_mat)

    vals = tf.matmul(coefs, inlayer)
    if act_func is None:
        return vals
    else:
        return act_func(vals)


def add_self_att_layer(inlayer, adj_mat, act_func, hid_dim):
    in_fts = tf.layers.conv1d(tf.expand_dims(
        inlayer, 0), hid_dim, 1, use_bias=False)
    f_1 = tf.reshape(tf.layers.conv1d(in_fts, 1, 1), (-1, 1))
    f_2 = tf.reshape(tf.layers.conv1d(in_fts, 1, 1), (-1, 1))
    logits = f_1 + tf.transpose(f_2)
    print('adding self attention layer...')
    adj_tensor = tf.constant(adj_mat, dtype=tf.float32)
    logits = tf.multiply(adj_tensor, logits)
    bias_mat = -1e9 * (1.0 - (adj_mat > 0))
    # eq (4)
    coefs = tf.nn.softmax(tf.nn.leaky_relu(logits) + bias_mat)

    # eq (3)
    vals = tf.matmul(coefs, inlayer)
    if act_func is None:
        return vals
    else:
        return act_func(vals)


def highway(layer1, layer2, dimension):
    kernel_gate = glorot([dimension, dimension])
    bias_gate = zeros([dimension])
    transform_gate = tf.matmul(layer1, kernel_gate) + bias_gate
    transform_gate = tf.nn.sigmoid(transform_gate)
    carry_gate = 1.0 - transform_gate
    return transform_gate * layer2 + carry_gate * layer1

# eq 5
def compute_r(inlayer, head_r, tail_r, dimension):
    head_l = tf.transpose(tf.constant(head_r, dtype=tf.float32))
    tail_l = tf.transpose(tf.constant(tail_r, dtype=tf.float32))
    L = tf.matmul(head_l, inlayer) / \
        tf.expand_dims(tf.reduce_sum(head_l, axis=-1), -1)
    R = tf.matmul(tail_l, inlayer) / \
        tf.expand_dims(tf.reduce_sum(tail_l, axis=-1), -1)
    r_embeddings = tf.concat([L, R], axis=-1)
    return r_embeddings


def get_dual_input(inlayer, head, tail, head_r, tail_r, dimension):
    dual_X = compute_r(inlayer, head_r, tail_r, dimension)
    print('computing the dual input...')
    count_r = len(head)
    # dual Graph 
    dual_A = np.zeros((count_r, count_r))
    for i in range(count_r):
        for j in range(count_r):
            # eq (2)
            a_h = len(head[i] & head[j]) / len(head[i] | head[j])
            a_t = len(tail[i] & tail[j]) / len(tail[i] | tail[j])
            # eq (1)
            dual_A[i][j] = a_h + a_t
    return dual_X, dual_A


def get_input_layer(e, dimension, lang, name_lose,raw_method):
    print('adding the primal input layer...')
    # name embeding?
    with open(file='data/' + lang + '_en/' + lang + '_vectorList.json', mode='r', encoding='utf-8') as f:
        embedding_list = json.load(f)
        print(len(embedding_list), 'rows,', len(embedding_list[0]), 'columns.')
    prop_embed_1 = np.load('data/{}_en/embed_{}.npy'.format(lang,lang)).astype(np.float32)
    prop_embed_2 = np.load('data/{}_en/embed_en.npy'.format(lang)).astype(np.float32)
    prop_embed = np.vstack((prop_embed_1,prop_embed_2))
    # to do: use more careful dimension reduce
    prop_embed = (prop_embed[:,0:300]+prop_embed[:,300:600])*0.5
    # prop_embed = tf.convert_to_tensor(prop_embed)
    input_embeddings = np.array(embedding_list,dtype=np.float32)
    print(type(prop_embed),type(input_embeddings))
    # input_embeddings = input_embeddings + prop_embed
    # name lose
    cnt = input_embeddings.shape[1]
    row = input_embeddings.shape[0]
    if raw_method:
        input_embeddings[:,0:cnt//100*name_lose]=np.random.random(size=(row,cnt//100*name_lose))
    else:
        input_embeddings[:,0:cnt//100*name_lose]=prop_embed[:,0:cnt//100*name_lose]
    input_embeddings = tf.convert_to_tensor(input_embeddings)
    prop_mebeddings = tf.convert_to_tensor(prop_embed)
    prop_mebeddings = tf.Variable(prop_mebeddings)
    ent_embeddings = tf.Variable(input_embeddings)
    return tf.nn.l2_normalize(ent_embeddings, 1), tf.nn.l2_normalize(prop_mebeddings, 1)


def get_loss(outlayer, ILL, gamma, k):
    print('getting loss...')
    left = ILL[:, 0]
    right = ILL[:, 1]
    t = len(ILL)
    left_x = tf.nn.embedding_lookup(outlayer, left)
    right_x = tf.nn.embedding_lookup(outlayer, right)
    A = tf.reduce_sum(tf.abs(left_x - right_x), 1)
    neg_left = tf.placeholder(tf.int32, [t * k], "neg_left")
    neg_right = tf.placeholder(tf.int32, [t * k], "neg_right")
    neg_l_x = tf.nn.embedding_lookup(outlayer, neg_left)
    neg_r_x = tf.nn.embedding_lookup(outlayer, neg_right)
    B = tf.reduce_sum(tf.abs(neg_l_x - neg_r_x), 1)
    C = - tf.reshape(B, [t, k])
    D = A + gamma
    L1 = tf.nn.relu(tf.add(C, tf.reshape(D, [t, 1])))
    neg_left = tf.placeholder(tf.int32, [t * k], "neg2_left")
    neg_right = tf.placeholder(tf.int32, [t * k], "neg2_right")
    neg_l_x = tf.nn.embedding_lookup(outlayer, neg_left)
    neg_r_x = tf.nn.embedding_lookup(outlayer, neg_right)
    B = tf.reduce_sum(tf.abs(neg_l_x - neg_r_x), 1)
    C = - tf.reshape(B, [t, k])
    L2 = tf.nn.relu(tf.add(C, tf.reshape(D, [t, 1])))
    return (tf.reduce_sum(L1) + tf.reduce_sum(L2)) / (2.0 * k * t)


def build(dimension, act_func, alpha, beta, gamma, k, lang, e, ILL,name_lose,raw_method, KG):
    tf.reset_default_graph()
    # 创建输入层 它是通过name嵌入到低维空间得到的
    # 注意这里是两个知识图谱name 的嵌入
    primal_X_0, prop_embeddings = get_input_layer(e, dimension, lang,name_lose,raw_method)
    # name lose
    # 通过关系三元组获取矩阵
    M, M_arr = get_sparse_tensor(e, KG)
    # 获得 关系head,tail记录,head tail关系矩阵 以及关系稀疏矩阵
    head, tail, head_r, tail_r, r_mat = rfunc(KG, e)

    print('first interaction...')
    # obtain relation represent and dual weight
    dual_X_1, dual_A_1 = get_dual_input(
        primal_X_0, head, tail, head_r, tail_r, dimension)
    # Dual attention layer
    dual_H_1 = add_self_att_layer(dual_X_1, dual_A_1, tf.nn.relu, 600)
    # Primary Attention layer
    primal_H_1 = add_sparse_att_layer(
        primal_X_0, dual_H_1, r_mat, tf.nn.relu, e)
    # eq (8)
    primal_X_1 = primal_X_0 + alpha * primal_H_1

    print('second interaction...')
    dual_X_2, dual_A_2 = get_dual_input(
        primal_X_1, head, tail, head_r, tail_r, dimension)
    dual_H_2 = add_dual_att_layer(
        dual_H_1, dual_X_2, dual_A_2, tf.nn.relu, 600)
    primal_H_2 = add_sparse_att_layer(
        primal_X_1, dual_H_2, r_mat, tf.nn.relu, e)
    if raw_method:
        primal_X_2 = primal_X_0 + beta * primal_H_2
    else:
        primal_X_2 = primal_X_0 + beta * primal_H_2 + 0.1 * prop_embeddings
    
    print('gcn layers...')
    gcn_layer_1 = add_diag_layer(
        primal_X_2, dimension, M, act_func, dropout=0.0)
    gcn_layer_1 = highway(primal_X_2, gcn_layer_1, dimension)
    gcn_layer_2 = add_diag_layer(
        gcn_layer_1, dimension, M, act_func, dropout=0.0)
    output_layer = highway(gcn_layer_1, gcn_layer_2, dimension)

    

    loss = get_loss(output_layer, ILL, gamma, k)
    return output_layer, loss


# get negative samples
def get_neg(ILL, output_layer, k):
    neg = []
    t = len(ILL)
    ILL_vec = np.array([output_layer[e1] for e1 in ILL])
    KG_vec = np.array(output_layer)
    sim = scipy.spatial.distance.cdist(ILL_vec, KG_vec, metric='cityblock')
    for i in range(t):
        rank = sim[i, :].argsort()
        neg.append(rank[0:k])

    neg = np.array(neg)
    neg = neg.reshape((t * k,))
    return neg


def training(output_layer, loss, learning_rate, epochs, ILL, e, k, test):
    # 创建 Adam 优化器。 使用优化器更新模型参数
    train_step = tf.train.AdamOptimizer(learning_rate).minimize(loss)
    print('initializing...')
    #  初始化模型参数
    init = tf.global_variables_initializer()
    # 创建 TensorFlow 会话
    sess = tf.Session()
    sess.run(init)
    print('running...')
    J = []
    t = len(ILL)
    ILL = np.array(ILL)
    L = np.ones((t, k)) * (ILL[:, 0].reshape((t, 1)))
    neg_left = L.reshape((t * k,))
    L = np.ones((t, k)) * (ILL[:, 1].reshape((t, 1)))
    neg2_right = L.reshape((t * k,))
    for i in range(epochs):
        if i % 10 == 0:
            out = sess.run(output_layer)
            neg2_left = get_neg(ILL[:, 1], out, k)
            neg_right = get_neg(ILL[:, 0], out, k)
            feeddict = {"neg_left:0": neg_left,
                        "neg_right:0": neg_right,
                        "neg2_left:0": neg2_left,
                        "neg2_right:0": neg2_right}

        _, th = sess.run([train_step, loss], feed_dict=feeddict)
        if i % 10 == 0:
            th, outvec = sess.run([loss, output_layer], feed_dict=feeddict)
            J.append(th)
            get_hits(outvec, test)

        print('%d/%d' % (i + 1, epochs), 'epochs...', th)
    outvec = sess.run(output_layer)
    sess.close()
    return outvec, J
