
def swipess(arr):
    arr[0]=arr[2]
a=[1,2]
b=[2,3,4,5]
swipess(b)
print(b)
print(a+b)
print(b[:-1])
sa =set([1,2])
sb =set([1,3])
print(sa|sb)

A={(1,2):1,(1,3):2}

for k,v in A:
    print(k,v)


B=[{k} for k in range(3)]

print(B)
print(type(B[0]))
from deep_translator import LingueeTranslator

from DataProc import *


root = './data/fr_en/'
root2 = '../explore-and-evaluate-main/bin/DBP15k/fr_en/'
id2ent1 = read_map(root+'ent_ids_1')
id2ent2 = read_map(root+'ent_ids_2')

ap2,np2 = read_prop(root2 + 'atts_properties_en.txt')
ap1,np1 = read_prop(root2 + 'atts_properties_fr.txt')
print(id2ent1[2])
print(np2['http://dbpedia.org/resource/Alabama'])
print(ap2['http://dbpedia.org/resource/Alabama'])
print('1 2',len(id2ent1),len(id2ent2))
print('length of prop{},{}'.format(len(ap1),len(ap2)))
cp1 = compact_prop(id2ent1,ap1)
cp2 = compact_prop(id2ent2,ap2)
print('length of cprop{},{}'.format(len(cp1),len(cp2)))
# td = translate_byblock(['auteur','fr'],'french')
# print(td)
# prop = trans_prop(ap1,'french')
save_prop('prop_fr.txt',id2ent1,ap1)
save_prop('prop_en.txt',id2ent2,ap2)
save_prop('propd_fr.txt',id2ent1,np1)
save_prop('propd_en.txt',id2ent2,np2)
split_file('prop_fr.txt',200000)
combine_file(['prop_frt._0.txt','prop_frt._1.txt'],'prop_fr_t.txt')



save_prop_cnt('pro_cnt_fr.txt',count_prop(ap1))
save_prop_cnt('pro_cnt_en.txt',count_prop(ap2))


