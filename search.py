from sentence_transformers import SentenceTransformer, util
import torch
import os

embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Corpus with example sentences
corpus = ['A man is eating food.',
          'A man is eating a piece of bread.',
          'The girl is carrying a baby.',
          'A man is riding a horse.',
          'A woman is playing violin.',
          'Two men pushed carts through the woods.',
          'A man is riding a white horse on an enclosed ground.',
          'A monkey is playing drums.',
          'A cheetah is running behind its prey.'
          ]
corpus_embeddings = embedder.encode(corpus, convert_to_tensor=True)
# Query sentences:
queries = ['A man is eating pasta.', 'Someone in a gorilla costume is playing a set of drums.', 'A cheetah chases prey on across a field.']

# Given a list of embeddings gives the score of the top sentence that matches the query embedding
def search(query, corpus_embeddings, corpus):
    query_embedding = embedder.encode(query, convert_to_tensor=True)

    # We use cosine-similarity and torch.topk to find the highest 5 scores
    cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
    top_results = torch.topk(cos_scores, 1)
    print("\n\n======================\n\n")
    print("Query:", query)
    print("\nTop most similar sentence in corpus:")

    for score, idx in zip(top_results[0], top_results[1]):
      print(corpus[idx], "(Score: {:.4f})".format(score))
    
    print(top_results[0][0], top_results[1][0])
    return top_results[0][0]

def search_file(query, file_name):
  # prep the infile
  new_file_name = os.path.basename(file_name)
  infile = 'indices/' + os.path.splitext(new_file_name)[0] + '_index.pt'
  query_embedding = embedder.encode(query, convert_to_tensor=True)
  cos_scores = util.cos_sim(query_embedding, torch.load(infile))[0]
  top_result = torch.topk(cos_scores, 1)

  score = top_result[0][0]
  index = int(top_result[1][0])
  text = ''

 
  with open(file_name, "r") as in_file:
    i = 0
    for line in in_file:
      if i == index:
        text = line
        break
      i += 1

  return(text, score, file_name)

def search_directory(query, directory):
  results = []
  for file_name in os.listdir(directory):
    results.append(search_file(query, os.path.join(directory, file_name)))
  
  results = sorted(results, key = lambda x: x[1], reverse = True)
  results_len = len(results)
  i = 0
  while i < 5 and i < results_len:
    print("\n=========================")
    print("Result {}: {}".format(i+1, results[i][2]))
    print("Text found: {}".format(results[i][0]))
    print("Relevancy: {}".format(results[i][1]))
    print("=========================")
    i += 1
  
  return results


def index(file_name, directory = None):
  tensor_list = []
  with open(file_name, "r") as in_file:
    for line in in_file:
      tensor_list.append(line)
  new_tensors = embedder.encode(tensor_list, convert_to_tensor=True)
  
  file_name = os.path.basename(file_name)
  save_location = os.path.splitext(file_name)[0] + '_index.pt'
  torch.save(new_tensors, os.path.join('indices', save_location))

def return_result(file_name):
  file_name = os.path.basename(file_name)
  outfile = 'audio/' + os.path.splitext(file_name)[0] + '.wav'
  print('Path to audio:' + outfile)


index('transcriptions/file1.txt', 1)
index('transcriptions/file2.txt', 1)
index('transcriptions/file3.txt', 1)

search_directory('A man is eating pasta.', 'transcriptions')
