"""
Hybrid RAG: Combine GraphRAG (Neo4j entities/relations) with standard vector RAG over article chunks.

Dependencies: neo4j, numpy, sentence-transformers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from time import perf_counter
from typing import Dict, List, Optional, Tuple

from neo4j import Driver, GraphDatabase

try:
    from neo4j.exceptions import ServiceUnavailable as Neo4jServiceUnavailable
except Exception:  # pragma: no cover
    Neo4jServiceUnavailable = Exception

from rag import vector_index
from utils.embedding_generator import EmbeddingGenerator


@dataclass
class RetrievedEntity:
    id: str
    name: str
    type: str
    description: str
    similarity: float


@dataclass
class RetrievedDoc:
    score: float
    article_id: str
    title: str
    url: str
    text: str


class HybridRAG:
    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        articles_dir: str = "data/articles",
        embedding_backend: str = "sentence_transformers",
        sentence_model_name: Optional[str] = None,
        index_max_files: Optional[int] = None,
        index_max_chunks_per_file: Optional[int] = None,
        index_chunk_progress_every: int = 50,
        resume_index: bool = False,
    ):
        self.driver: Driver = GraphDatabase.driver(
            neo4j_uri, auth=(neo4j_user, neo4j_password)
        )
        self.embedding = EmbeddingGenerator(
            self.driver,
            embedding_model=(embedding_backend or "sentence_transformers"),
            sentence_model_name=sentence_model_name,
        )
        self.verbose = False
        # Backward-compatible: allow passing via env RAG_VERBOSE=1
        try:
            import os as _os

            self.verbose = _os.getenv("RAG_VERBOSE", "0") == "1"
        except Exception:
            self.verbose = False
        # Ensure vector index exists
        if self.embedding.embedding_function is None:
            raise RuntimeError(
                "Embedding function is not initialized. Install and configure sentence-transformers."
            )
        t0 = perf_counter()
        vector_index.ensure_index(
            articles_dir,
            self.embedding.embedding_function,
            verbose=self.verbose,
            max_files=index_max_files,
            max_chunks_per_file=index_max_chunks_per_file,
            chunk_progress_every=index_chunk_progress_every,
            resume=resume_index,
        )
        if self.verbose:
            print(f"[HybridRAG] Vector index ready in {perf_counter() - t0:.2f}s")

    def close(self):
        self.driver.close()

    def _get_graph_context(
        self, query: str, top_k_entities: int = 5, neighbor_hops: int = 1
    ) -> Tuple[List[RetrievedEntity], List[Dict], List[str]]:
        """
        Returns:
            - top entities
            - relationship triples for context [{source, type, target}]
            - related article_ids (strings)
        """
        if self.verbose:
            print(f"[HybridRAG] Finding similar entities (top={top_k_entities})...")
        t0 = perf_counter()
        similar = self.embedding.find_similar_entities(query, limit=top_k_entities)
        if self.verbose:
            print(
                f"[HybridRAG] Found {len(similar)} entities in {perf_counter() - t0:.2f}s"
            )
        entities: List[RetrievedEntity] = [
            RetrievedEntity(
                id=e.get("id", ""),
                name=e.get("name", ""),
                type=e.get("type", ""),
                description=e.get("description", ""),
                similarity=float(e.get("similarity", 0.0)),
            )
            for e in similar
        ]

        if not entities:
            return [], [], []

        entity_ids = [e.id for e in entities if e.id]
        rels: List[Dict] = []
        article_ids: List[str] = []
        with self.driver.session() as s:
            # Neighbor relationships
            if self.verbose:
                print(
                    f"[HybridRAG] Expanding neighbors (hops={neighbor_hops}) and collecting relationships..."
                )
            t1 = perf_counter()
            result = s.run(
                f"""
                MATCH (e) WHERE e.id IN $entity_ids
                MATCH path = (e)-[r*1..{neighbor_hops}]-(n)
                WITH relationships(path) as rels, nodes(path) as ns
                UNWIND rels as rel
                WITH DISTINCT startNode(rel) as s, endNode(rel) as t, type(rel) as rt
                RETURN s.name as sname, labels(s)[0] as slabel, rt as rel_type, t.name as tname, labels(t)[0] as tlabel
                LIMIT 200
                """,
                entity_ids=entity_ids,
            )
            for r in result:
                rels.append(
                    {
                        "source": f"{r['sname']} ({r['slabel']})",
                        "type": r["rel_type"],
                        "target": f"{r['tname']} ({r['tlabel']})",
                    }
                )
            if self.verbose:
                print(
                    f"[HybridRAG] Relationships collected: {len(rels)} in {perf_counter() - t1:.2f}s"
                )

            # Source articles from entities
            if self.verbose:
                print("[HybridRAG] Gathering source articles from entities...")
            t2 = perf_counter()
            result2 = s.run(
                """
                MATCH (e) WHERE e.id IN $entity_ids AND e.source_articles IS NOT NULL
                UNWIND e.source_articles as aid
                RETURN DISTINCT aid as article_id
                LIMIT 200
                """,
                entity_ids=entity_ids,
            )
            for r in result2:
                article_ids.append(r["article_id"])
            if self.verbose:
                print(
                    f"[HybridRAG] Article IDs collected: {len(article_ids)} in {perf_counter() - t2:.2f}s"
                )

        return entities, rels, article_ids

    def _get_vector_docs(self, query: str, top_k_docs: int = 5) -> List[RetrievedDoc]:
        if self.embedding.embedding_function is None:
            return []
        if self.verbose:
            print(f"[HybridRAG] Vector search (top={top_k_docs})...")
        t0 = perf_counter()
        docs = vector_index.search(
            query, self.embedding.embedding_function, top_k=top_k_docs
        )
        if self.verbose:
            print(
                f"[HybridRAG] Vector search returned {len(docs)} in {perf_counter() - t0:.2f}s"
            )
        return [
            RetrievedDoc(
                score=d["score"],
                article_id=d["article_id"],
                title=d.get("title", ""),
                url=d.get("url", ""),
                text=d.get("text", ""),
            )
            for d in docs
        ]

    def query(
        self,
        question: str,
        top_k_entities: int = 5,
        top_k_docs: int = 5,
        neighbor_hops: int = 1,
        vector_only: bool = False,
    ) -> Dict:
        if self.verbose:
            print("[HybridRAG] Starting hybrid retrieval...")
        t0 = perf_counter()
        entities: List[RetrievedEntity] = []
        rels: List[Dict] = []
        graph_article_ids: List[str] = []
        if not vector_only:
            try:
                entities, rels, graph_article_ids = self._get_graph_context(
                    question, top_k_entities=top_k_entities, neighbor_hops=neighbor_hops
                )
            except Neo4jServiceUnavailable as e:
                if self.verbose:
                    print(
                        f"[HybridRAG] Neo4j unavailable, falling back to vector-only: {e}"
                    )
            except Exception as e:
                if self.verbose:
                    print(
                        f"[HybridRAG] Graph context error, continuing vector-only: {e}"
                    )
        vector_docs = self._get_vector_docs(question, top_k_docs=top_k_docs)

        # Pull best chunks for graph-derived articles from vector index to include text
        # (reuse vector index metadata if available)
        extra_graph_docs: List[RetrievedDoc] = []
        emb, chunks, meta = vector_index.load_index()
        art2chunks = meta.get("article_to_chunk_ids", {}) if meta else {}
        chunk_by_id = {c.chunk_id: c for c in chunks}
        for aid in graph_article_ids[: top_k_docs * 2]:
            for cid in art2chunks.get(aid, [])[
                :1
            ]:  # take one representative chunk per article
                ch = chunk_by_id.get(cid)
                if ch:
                    extra_graph_docs.append(
                        RetrievedDoc(
                            score=0.0,  # score will be set by fusion
                            article_id=ch.article_id,
                            title=ch.title,
                            url=ch.url,
                            text=ch.text,
                        )
                    )

        # Fusion: simple weighted merge and rerank (graph signal + vector score)
        # - Vector docs keep their cosine score in [0,1] approx (not strictly)
        # - Graph docs get score from max entity similarity involved (fallback 0.5)
        max_ent_sim = max((e.similarity for e in entities), default=0.5)

        merged: Dict[Tuple[str, str], RetrievedDoc] = {}

        def key(d: RetrievedDoc) -> Tuple[str, str]:
            return (d.article_id, d.title)

        for d in vector_docs:
            merged[key(d)] = d

        for d in extra_graph_docs:
            if key(d) in merged:
                # Boost existing score using graph signal
                merged[key(d)].score = float(
                    0.7 * merged[key(d)].score + 0.3 * max_ent_sim
                )
            else:
                d.score = float(0.3 * max_ent_sim)
                merged[key(d)] = d

        final_docs = sorted(merged.values(), key=lambda x: x.score, reverse=True)[
            :top_k_docs
        ]
        if self.verbose:
            print(
                f"[HybridRAG] Fusion complete in {perf_counter() - t0:.2f}s | entities={len(entities)} rels={len(rels)} docs={len(final_docs)}"
            )

        # Prepare a compact graph context string
        graph_facts = []
        for r in rels[:10]:
            graph_facts.append(f"{r['source']} -[{r['type']}]-> {r['target']}")

        return {
            "question": question,
            "entities": [e.__dict__ for e in entities],
            "graph_facts": graph_facts,
            "contexts": [
                {
                    "title": d.title,
                    "url": d.url,
                    "article_id": d.article_id,
                    "score": d.score,
                    "text": d.text,
                }
                for d in final_docs
            ],
        }


def _format_answer_input(payload: Dict) -> str:
    parts: List[str] = []
    if payload.get("graph_facts"):
        parts.append("Graph facts:\n" + "\n".join(payload["graph_facts"]))
    for i, c in enumerate(payload.get("contexts", []), 1):
        parts.append(f"Doc {i} (score={c['score']:.3f}) - {c['title']}\n{c['text']}")
    return "\n\n".join(parts)


def answer_with_openai(payload: Dict, model: str = "gpt-4o-mini") -> str:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception as e:
        return f"OpenAI not available: {e}"

    context = _format_answer_input(payload)
    question = payload.get("question", "")
    messages = [
        {
            "role": "system",
            "content": "You are a precise assistant. Cite facts from the provided context only.",
        },
        {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"},
    ]
    try:
        resp = client.chat.completions.create(
            model=model, messages=messages, temperature=0.2
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"Answer generation failed: {e}"


def main():
    import argparse

    from dotenv import load_dotenv

    load_dotenv()
    parser = argparse.ArgumentParser(description="Hybrid RAG query")
    parser.add_argument("question", type=str, help="User question")
    parser.add_argument("--entities", type=int, default=5)
    parser.add_argument("--docs", type=int, default=5)
    parser.add_argument("--hops", type=int, default=1)
    parser.add_argument(
        "--verbose", action="store_true", help="Print progress and timings"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Limit number of files for index build",
    )
    parser.add_argument(
        "--max-chunks-per-file",
        type=int,
        default=None,
        help="Limit chunks per file during index build",
    )
    parser.add_argument(
        "--chunk-progress-every",
        type=int,
        default=50,
        help="Chunk progress print frequency",
    )
    parser.add_argument(
        "--vector-only",
        action="store_true",
        help="Skip graph step and use vector retrieval only",
    )
    parser.add_argument(
        "--resume-index",
        action="store_true",
        help="Resume/append to existing vector index if present",
    )
    parser.add_argument(
        "--embedding-backend",
        choices=["openai", "sentence-transformers"],
        default=os.getenv("RAG_EMBEDDING_BACKEND", "openai"),
        help="Embedding backend to use",
    )
    parser.add_argument(
        "--st-model",
        type=str,
        default=os.getenv("SENTENCE_TRANSFORMERS_MODEL", None),
        help="Sentence-Transformers model name (e.g., BAAI/bge-small-en-v1.5)",
    )
    args = parser.parse_args()

    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

    # Allow --verbose to force progress output
    if args.verbose:
        import os as _os

        _os.environ["RAG_VERBOSE"] = "1"

    if args.resume_index:
        os.environ["RAG_RESUME_INDEX"] = "1"

    rag = HybridRAG(
        neo4j_uri,
        neo4j_user,
        neo4j_password,
        embedding_backend=args.embedding_backend,
        sentence_model_name=args.st_model,
        index_max_files=args.max_files,
        index_max_chunks_per_file=args.max_chunks_per_file,
        index_chunk_progress_every=args.chunk_progress_every,
        resume_index=os.getenv("RAG_RESUME_INDEX", "0") == "1",
    )
    try:
        payload = rag.query(
            args.question,
            top_k_entities=args.entities,
            top_k_docs=args.docs,
            neighbor_hops=args.hops,
            vector_only=args.vector_only,
        )
        print("===== Hybrid Retrieval Context =====\n")
        print(_format_answer_input(payload))
        print("\n===== Answer =====\n")
        print(answer_with_openai(payload))
    finally:
        rag.close()


if __name__ == "__main__":
    main()
