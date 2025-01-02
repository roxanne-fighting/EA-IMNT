from transformers import BertTokenizer, BertModel
# importing libraries
import random
import torch
import numpy as np
from DataProc import *

lang='zh'
root = './data/{}_en/'.format(lang)
kap1 = read_kprop(root+'prop_{}.txt'.format('en'))
save_name='embed_en.npy'
cap1 = compact_kprop(kap1)

sent1=[]
for k in cap1:
    sent1.append(cap1[k])
print(sent1[0:1])
print('sent1 num:',len(sent1))
Nsent = len(sent1)
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')
embed_dim = 768
Nstep=10
embeded= np.zeros((Nsent,embed_dim))
for i in range(Nsent//Nstep+1):
	# Tokenize and encode text using batch_encode_plus
	# The function returns a dictionary containing the token IDs and attention masks
	
	i2=min((i+1)*Nstep,Nsent)
	encoding = tokenizer.batch_encode_plus(
		sent1[i*Nstep:i2],				 # List of input texts
		padding=True,			 # Pad to the maximum sequence length
		truncation=True,		 # Truncate to the maximum sequence length if necessary
		return_tensors='pt',	 # Return PyTorch tensors
		add_special_tokens=True # Add special tokens CLS and SEP
	)

	input_ids = encoding['input_ids'] # Token IDs
	# print input IDs
	# print(f"Input ID: {input_ids}")
	attention_mask = encoding['attention_mask'] # Attention mask
	# print attention mask
	# print(f"Attention mask: {attention_mask}")


	# Generate embeddings using BERT model
	with torch.no_grad():
		outputs = model(input_ids, attention_mask=attention_mask)
		word_embeddings = outputs.last_hidden_state # This contains the embeddings

	# Output the shape of word embeddings
	# print(f"Shape of Word Embeddings: {word_embeddings.shape}")

	# Compute the average of word embeddings to get the sentence embedding
	sentence_embedding = word_embeddings.mean(dim=1) # Average pooling along the sequence length dimension

	# Print the sentence embedding
	# print("Sentence Embedding:")
	# print(sentence_embedding)

	# Output the shape of the sentence embedding
	# print(f"Shape of Sentence Embedding: {sentence_embedding.shape}")
	embeded[i*Nstep:i2,:]=sentence_embedding
	if i%10==0:
		print('embed:{}/{}'.format(i*Nstep,Nsent))
	if i2==Nsent:
		break

print('embed size is',embeded.shape)
np.save(root+save_name, embeded)







