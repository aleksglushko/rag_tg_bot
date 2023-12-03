from langchain.vectorstores import Qdrant
from langchain.text_splitter import CharacterTextSplitter, TextSplitter

qdrant_url = "http://localhost:6333"

db = await Qdrant.afrom_documents(documents, embeddings, qdrantdb_url)

query = "What did the president say about Ketanji Brown Jackson"
docs = await db.asimilarity_search(query)
print(docs[0].page_content)

# simi;arity seearch by vector
embedding_vector = embeddings.embed_query(query)
docs = await db.asimilarity_search_by_vector(embedding_vector)

