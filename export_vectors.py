import chromadb
import numpy as np
from pathlib import Path

client = chromadb.PersistentClient(path="./vector_db")
col = client.get_collection("research_abstracts")

data = col.get(include=["embeddings", "documents", "metadatas"])

out = Path("./vector_store_numpy")
out.mkdir(parents=True, exist_ok=True)

np.save(out / "embeddings.npy", np.array(data["embeddings"]))
np.save(out / "documents.npy", np.array(data["documents"], dtype=object))
np.save(out / "metadatas.npy", np.array(data["metadatas"], dtype=object))
np.save(out / "ids.npy", np.array(data["ids"]))

print(f"Exported {len(data['ids'])} chunks to vector_store_numpy/")