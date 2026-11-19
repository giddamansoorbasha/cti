# Lab 17: Local RAG Pipeline & Cross-Engine HNSW Vector Search Benchmark

## Required Containers & Services
* MongoDB Atlas Local: `cti-atlas-local` (`27777`, auth via `MONGODB_INITDB_ROOT_USERNAME` / `MONGODB_INITDB_ROOT_PASSWORD`)
* Neo4j: `cti-neo4j` (`7474`, `7687`, auth `neo4j/password`)
* Ollama (`http://localhost:11434`): `nomic-embed-text` and `llama3.2:3b`

## Scripts
* `01_rag_pipeline.py`: Embeds 6 threat chunks with `nomic-embed-text`, creates a filtered Atlas Vector Search index (`vector_index_lifecycle`), runs a platform-filtered `$vectorSearch` query, and generates a grounded answer with `llama3.2:3b`.
* `02_hnsw_vs_ivf.py`: Seeds 5,000 normalized 384-D vectors into MongoDB Atlas Local and Neo4j, benchmarks median/P95 latency and `recall@10`, and sweeps MongoDB HNSW build/query parameters (`maxEdges`, `numEdgeCandidates`, `numCandidates`).
* `upload_model_to_hf.py`: Utility script used to export the local `llama3.2:3b` GGUF model and metadata to Hugging Face (`gmansoor/Llama-3.2-3B-CTI-GGUF`).

## Run from `labs/` (Save to `output.txt`)

    $envVars = docker inspect cti-atlas-local --format '{{range .Config.Env}}{{println .}}{{end}}'; $u = ($envVars | Select-String '^MONGODB_INITDB_ROOT_USERNAME=').ToString().Split('=',2)[1]; $p = ($envVars | Select-String '^MONGODB_INITDB_ROOT_PASSWORD=').ToString().Split('=',2)[1]; $env:VECTOR_MONGO_URI = "mongodb://${u}:${p}@127.0.0.1:27777/?directConnection=true&authSource=admin"; & { echo "=== 01_rag_pipeline.py ==="; python -u -B lab17\01_rag_pipeline.py; echo "`n=== 02_hnsw_vs_ivf.py ==="; python -u -B lab17\02_hnsw_vs_ivf.py } | Tee-Object -FilePath lab17\output.txt

## Benchmark Summary (5,000 × 384-D, 100 Queries, Top-10 Cosine)
| Engine | Index | Median Latency | P95 Latency | Mean Recall@10 |
|---|---|---:|---:|---:|
| MongoDB Atlas Local | HNSW (`maxEdges=16`, `numCandidates=100`) | 8.82 ms | 21.04 ms | 95.2% |
| Neo4j | HNSW (native defaults) | 7.78 ms | 11.77 ms | 54.6% |

## Outputs
* `output.txt`