# tsun.dere Documentation

## What is tsun.dere?

**tsun.dere** is an anime and manga focused semantic search engine designed to provide highly relevant and context-aware results across titles, genres, characters, tags, and descriptions.

Rather than relying purely on keyword matching, tsun.dere combines multiple retrieval and ranking techniques including:

* BM25 lexical retrieval
* Custom weighted semantic indexing
* Cross-encoder reranking
* Redis-based caching
* MongoDB-backed processing pipelines

The objective is simple:

> Deliver fast and meaningful anime discovery with better semantic understanding.

---

# Search Architecture
![System](/achitecture.png)
The search pipeline in tsun.dere is designed as a hybrid retrieval system.

The engine first retrieves candidate documents quickly using BM25 and weighted indexing, then improves ranking quality using semantic reranking techniques.

Core stages:

1. Query preprocessing
2. BM25 candidate retrieval
3. Weighted semantic scoring
4. Cross-encoder reranking
5. Redis cache delivery
6. MongoDB-backed result refresh

---

# BM25 Indexing

## Why BM25?

BM25 is the primary lexical retrieval mechanism used by tsun.dere.

It performs extremely well for anime and manga search because users often search using:

* partial titles,
* genres,
* tags,
* themes,
* or descriptive phrases.

Example queries:

```text
psychological cyberpunk anime
```

```text
romance anime with tsundere lead
```

BM25 allows the engine to efficiently retrieve documents with strong lexical relevance before semantic refinement takes place.

---

## BM25 Formula

BM25(D,Q)=\sum_{i=1}^{n} IDF(q_i) \cdot \frac{f(q_i,D)(k_1+1)}{f(q_i,D)+k_1\left(1-b+b\cdot\frac{|D|}{avgdl}\right)}

BM25 scoring helps balance:

* term importance,
* term frequency,
* and document length normalization.

This prevents overly long descriptions from dominating rankings while still rewarding highly relevant matches.

---

# Custom Weighted Semantic Indexing

Pure lexical matching is insufficient for anime discovery.

Users frequently search using emotional, thematic, or aesthetic language such as:

```text
melancholic lonely protagonist
```

```text
slow atmospheric mystery anime
```

To improve semantic relevance, tsun.dere applies custom weighting to indexed fields.

Example weighted fields include:

| Field              | Relative Importance |
| ------------------ | ------------------- |
| Title              | Very High           |
| Alternative Titles | High                |
| Genres             | High                |
| Tags               | High                |
| Synopsis           | Medium              |
| Character Metadata | Medium              |

This allows semantically important fields to contribute more heavily during ranking.

For example, a direct genre or tag match should generally outrank a weak mention inside a long synopsis.

---

# Semantic Expansion

tsun.dere also performs semantic expansion during retrieval.

This includes:

* synonym mapping,
* alias resolution,
* related tag expansion,
* and franchise-aware associations.

Example:

| Query     | Expanded Context         |
| --------- | ------------------------ |
| mecha     | robots, giant robots     |
| iyashikei | healing, relaxing        |
| tsundere  | cold affection archetype |

This improves retrieval quality for users who search using community terminology or thematic descriptors.

---

# Cross-Encoder Reranking

After initial retrieval, tsun.dere applies a **cross-encoder reranking stage** to improve final relevance ordering.

The first-stage retriever focuses on speed and broad recall.

The reranker focuses on precision.

---

## Why Reranking Matters

Initial retrieval may return many partially relevant results.

Example query:

```text
anime about identity and isolation
```

Traditional retrieval systems may prioritize documents containing exact terms, but fail to understand deeper contextual meaning.

Cross-encoders analyze:

* the query,
* and candidate document text together,

allowing the model to better understand semantic relationships and contextual intent.

---

## Retrieval Strategy

The pipeline generally works as:

1. BM25 retrieves candidate documents
2. Weighted semantic scoring refines candidates
3. Top candidate set is passed into the cross-encoder
4. Cross-encoder produces final relevance ordering

This hybrid architecture balances:

* retrieval speed,
* scalability,
* and semantic accuracy.

---

# Redis Cache Layer

tsun.dere uses Redis as a high-speed cache layer to reduce perceived latency and avoid unnecessary recomputation.

Search requests can involve:

* ranking pipelines,
* semantic expansion,
* reranking stages,
* and aggregation operations.

Some operations may take noticeable time depending on query complexity and indexing state.

Redis allows the system to immediately return previously computed results while background processing continues.

---

# Cached Response Strategy

When a query is repeated:

1. Cached results are returned immediately from Redis
2. The frontend displays results instantly
3. MongoDB-backed processing refreshes results asynchronously
4. Updated rankings are written back into Redis

This creates a responsive search experience even during expensive processing operations.

The cache layer effectively follows a:

```text
stale-while-revalidate
```

style retrieval strategy.

---

# MongoDB Processing

MongoDB is used for:

* persistent search metadata,
* document storage,
* indexing pipelines,
* and retrieval processing.

Heavy processing and ranking operations are performed against MongoDB-backed datasets before refreshed results are cached again through Redis.

---

# Ranking Philosophy

Final ranking quality is determined through a combination of:

* BM25 lexical relevance
* Semantic weighting
* Contextual expansion
* Cross-encoder reranking
* Metadata-aware scoring

The system is designed to prioritize:

1. strong exact matches,
2. semantic intent,
3. thematic similarity,
4. and contextual relevance.

---

# Performance Goals

tsun.dere is optimized around:

| Metric                  | Goal                    |
| ----------------------- | ----------------------- |
| Cached query latency    | Near-instant            |
| Fresh retrieval latency | Low seconds             |
| Retrieval scalability   | Horizontally scalable   |
| Search quality          | High semantic relevance |

---

# Example Queries

```text
sad cyberpunk anime
```

```text
anime with unreliable narrator
```

```text
romance anime with emotionally distant lead
```

```text
retro psychological thriller
```

```text
anime similar to serial experiments lain
```

---

# Tech Stack

| Component        | Technology             |
| ---------------- | ---------------------- |
| Backend          | FastAPI                |
| Database         | MongoDB                |
| Cache Layer      | Redis                  |
| Retrieval Engine | BM25 + Custom Indexing |
| Reranking        | Cross-Encoder Models   |
| API              | REST                   |
| Frontend         | React                  |

---

# Closing Notes

tsun.dere is built specifically for anime and manga discovery rather than generic media retrieval.

The engine combines traditional information retrieval techniques with semantic ranking and modern reranking pipelines to create a search experience focused on:

* contextual understanding,
* fast response times,
* and higher quality discovery.
