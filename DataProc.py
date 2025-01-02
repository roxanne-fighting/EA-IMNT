
# id to entity
def read_map(fn):
    print('loading a file...' + fn)
    ret = {}
    with open(fn, encoding='utf-8') as f:
        for line in f:
            th = line[:-1].split('\t')
            ret[int(th[0])]=th[1]
    return ret

# entity prop
def read_prop(fn):
    print('loading a file...' + fn)
    a_literal = {}
    n_literal = {}
    with open(fn, encoding='utf-8') as f:
        for line in f:
            th = line[:-1].split('\t')
            if (th[3][-6:]=='double' or th[3][-7:]=='integer'):
                s = th[2].replace(',','')
                s = s.replace(' ','')
                if th[0] not in n_literal:
                    n_literal[th[0]]=[]
                try:
                    n_literal[th[0]].append((th[1], float(s)))
                except:
                    n_literal[th[0]].append((th[1], 0))
            else:
                if th[0] not in a_literal:
                    a_literal[th[0]]=[]
                a_literal[th[0]].append((th[1], th[2]))
    return a_literal, n_literal

def read_kprop(fn):
    prop={}
    with open(fn, encoding='utf-8') as f:
        for line in f:
            th = line[:-1].split('\t')
            k = int(th[0])
            if k not in prop:
                prop[k]=[]
            prop[k].append((th[1], th[2]))
    return prop

# save prop by id
def save_prop(fn,id2ent,prop):
    with open(fn,'w',encoding='utf-8') as f:
        for k in id2ent:
            if id2ent[k] in prop:
                for v in prop[id2ent[k]]:
                    f.writelines('{}\t{}\t{}\n'.format(k,v[0],v[1]))
            else:
                f.writelines('{}\t-\t-\n'.format(k))

def compact_prop(id2ent, prop):
    cpact_prop={}
    for k in id2ent:
        sent = ''
        if id2ent[k] in prop:
            for v in prop[id2ent[k]]:
                sent += v[0] +' ' +v[1] + ' '
        cpact_prop[k]=sent
    return cpact_prop


def compact_kprop(prop):
    cpact_prop={}
    for k in prop:
        sent = ''
        for v in prop[k]:
            sent += v[0] +' ' +v[1] + ' '
        cpact_prop[k]=sent
    return cpact_prop

def save_prop_cnt(fn,cnt):
     with open(fn,'w',encoding='utf-8') as f:
        for k in cnt:
            f.write('{}\t{}\n'.format(k,cnt[k]))

def split_file(fn,maxlines):
     cnt=0
     id=0
     f2 = open('{}_{}.txt'.format(fn[:-3],id),'w', encoding='utf-8')
     with open(fn,'r',encoding='utf-8') as f:
        for line in f:
            if cnt<maxlines:
                cnt+=1
                f2.write(line)
            else:
                cnt=0
                id+=1
                f2.close()
                f2 = open('{}_{}.txt'.format(fn[:-3],id),'w', encoding='utf-8')
                cnt+=1
                f2.write(line)
        if cnt>0:
            id+=1
            f2.close()

def combine_file(files,ft):
     f2 = open(ft,'w',encoding='utf-8')
     for fn in files:
        with open(fn,'r',encoding='utf-8') as f:
            for line in f:
                f2.write(line)
            f.close()
          

def trans_prop(prop,lng):
    tprop={}
    c =[]
    id=0
    for e in prop:
        for pp in prop[e]:
            c.append(pp[0])
            c.append(pp[1])
            id+=2
    ct = translate_byblock(c,lng)
    id=0
    for e in prop:
        tprop[e]=[]
        for pp in prop[e]:
            val = (ct[id],ct[id+1])
            tprop[e].append(val)
            id+=2
    return tprop

def count_prop(ap):
    cnt={}
    for e in ap:
        for k in ap[e]:
            if k[0] not in cnt:
                cnt[k[0]]=1
            else:
                cnt[k[0]]+=1
    return cnt