"""Topic clustering using BERTopic with HDBSCAN + UMAP."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import TopicCluster, TopicGraph, TopicLink

logger = get_logger(__name__)

_embedding_model = None
_executor = ThreadPoolExecutor(max_workers=2)


def _load_embedding_model():
    global _embedding_model
    if _embedding_model is not None:
        return

    try:
        from sentence_transformers import SentenceTransformer

        model_name = settings.embedding_model
        logger.info("loading_embedding_model", model=model_name)
        _embedding_model = SentenceTransformer(
            model_name,
            cache_folder=settings.model_cache_dir,
        )
        logger.info("embedding_model_loaded", model=model_name)
    except Exception as exc:
        logger.error("embedding_model_load_failed", error=str(exc))
        raise


def _compute_embeddings(texts: list[str]) -> np.ndarray:
    _load_embedding_model()
    return _embedding_model.encode(
        texts,
        show_progress_bar=False,
        batch_size=64,
        normalize_embeddings=True,
    )


def _adaptive_params(n_docs: int) -> dict:
    """Adapt HDBSCAN/UMAP parameters to data volume."""
    if n_docs < 20:
        return {"min_cluster_size": 2, "min_samples": 1, "n_neighbors": 3, "n_components": 2}
    elif n_docs < 100:
        return {"min_cluster_size": 3, "min_samples": 2, "n_neighbors": 5, "n_components": 3}
    elif n_docs < 500:
        return {"min_cluster_size": 5, "min_samples": 3, "n_neighbors": 10, "n_components": 5}
    elif n_docs < 2000:
        return {"min_cluster_size": 10, "min_samples": 5, "n_neighbors": 15, "n_components": 5}
    else:
        return {"min_cluster_size": 15, "min_samples": 8, "n_neighbors": 15, "n_components": 10}


def _cluster_topics_sync(
    texts: list[str],
    embeddings: np.ndarray | None = None,
    min_cluster_size: int | None = None,
    min_samples: int | None = None,
) -> tuple[list[int], list[TopicCluster], np.ndarray | None]:
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP

    if embeddings is None:
        embeddings = _compute_embeddings(texts)

    params = _adaptive_params(len(texts))
    mcs = min_cluster_size or params["min_cluster_size"]
    ms = min_samples or params["min_samples"]

    umap_model = UMAP(
        n_neighbors=params["n_neighbors"],
        n_components=params["n_components"],
        min_dist=0.0,
        metric="cosine",
        random_state=42,
    )

    hdbscan_model = HDBSCAN(
        min_cluster_size=mcs,
        min_samples=ms,
        metric="euclidean",
        prediction_data=True,
    )

    vectorizer = CountVectorizer(
        stop_words="english",
        max_features=10000,
        ngram_range=(1, 2),
    )

    topic_model = BERTopic(
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer,
        calculate_probabilities=True,
        verbose=False,
    )

    topics, probs = topic_model.fit_transform(texts, embeddings)

    topic_info = topic_model.get_topic_info()
    clusters = []

    for _, row in topic_info.iterrows():
        tid = int(row["Topic"])
        if tid == -1:
            label = "Uncategorized"
            keywords = []
        else:
            topic_words = topic_model.get_topic(tid)
            keywords = [w for w, _ in topic_words[:10]] if topic_words else []
            label = " | ".join(keywords[:3]) if keywords else f"Topic {tid}"

        indices = [i for i, t in enumerate(topics) if t == tid]
        rep_docs = [texts[i][:200] for i in indices[:3]]

        clusters.append(
            TopicCluster(
                topic_id=tid,
                label=label,
                keywords=keywords,
                size=int(row.get("Count", len(indices))),
                avg_sentiment=0.0,
                sentiment_distribution={"positive": 0, "negative": 0, "neutral": 0},
                languages={},
                representative_docs=rep_docs,
            )
        )

    # Get 2D coordinates for visualization
    reduced = None
    if len(texts) > 2:
        try:
            umap_2d = UMAP(n_components=2, random_state=42, metric="cosine")
            reduced = umap_2d.fit_transform(embeddings)
        except Exception:
            pass

    return topics, clusters, reduced


def build_topic_graph(clusters: list[TopicCluster], embeddings: np.ndarray, topics: list[int]) -> TopicGraph:
    """Build force-directed graph from topic clusters."""
    from sklearn.metrics.pairwise import cosine_similarity

    unique_topics = list({c.topic_id for c in clusters if c.topic_id != -1})
    links = []

    if len(unique_topics) > 1:
        centroids = []
        for tid in unique_topics:
            indices = [i for i, t in enumerate(topics) if t == tid]
            if indices:
                centroid = embeddings[indices].mean(axis=0)
                centroids.append(centroid)
            else:
                centroids.append(np.zeros(embeddings.shape[1]))

        sim_matrix = cosine_similarity(np.array(centroids))

        for i, t1 in enumerate(unique_topics):
            for j, t2 in enumerate(unique_topics):
                if i < j and sim_matrix[i][j] > 0.1:
                    links.append(
                        TopicLink(
                            source=t1,
                            target=t2,
                            weight=round(float(sim_matrix[i][j]), 4),
                        )
                    )

    return TopicGraph(nodes=clusters, links=links)


async def cluster_topics(
    texts: list[str],
    embeddings: np.ndarray | None = None,
    min_cluster_size: int | None = None,
    min_samples: int | None = None,
) -> tuple[list[int], list[TopicCluster], np.ndarray | None]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, _cluster_topics_sync, texts, embeddings, min_cluster_size, min_samples
    )


async def compute_embeddings(texts: list[str]) -> np.ndarray:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _compute_embeddings, texts)


_embedding_available: bool | None = None


def is_embedding_model_available() -> bool:
    """Check if embedding model is available. Re-checks on each call until successful."""
    global _embedding_available
    if _embedding_available is True:
        return True
    try:
        _load_embedding_model()
        _embedding_available = True
        logger.info("embedding_model_availability", available=True)
    except Exception as exc:
        _embedding_available = False
        logger.warning("embedding_model_availability", available=False, error=str(exc))
    return _embedding_available
