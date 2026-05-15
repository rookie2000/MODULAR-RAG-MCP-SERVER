"""Custom evaluator implementation for lightweight metrics.

This evaluator computes simple, deterministic metrics such as hit rate and MRR.
It is designed for fast regression checks and sanity validation.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from src.libs.evaluator.base_evaluator import BaseEvaluator


class CustomEvaluator(BaseEvaluator):
    """Custom evaluator for lightweight metrics (hit_rate, mrr).

    The evaluator expects retrieved chunks to contain an identifier field.
    Supported id fields: id, chunk_id, document_id, doc_id.
    """

    SUPPORTED_METRICS = {"hit_rate", "mrr", "faithfulness", "answer_similarity"}
    _ID_FIELDS = ("id", "chunk_id", "document_id", "doc_id")
    _SOURCE_FIELDS = ("source_path", "source", "file_path", "path")

    def __init__(
        self,
        settings: Any = None,
        metrics: Sequence[str] | None = None,
        **kwargs: Any,
    ) -> None:
        self.settings = settings
        self.kwargs = kwargs

        if metrics is None:
            metrics = self._metrics_from_settings(settings)

        normalized = [str(metric).strip().lower() for metric in (metrics or [])]
        if not normalized:
            normalized = ["hit_rate", "mrr"]

        unsupported = [metric for metric in normalized if metric not in self.SUPPORTED_METRICS]
        if unsupported:
            raise ValueError(
                "Unsupported custom metrics: "
                f"{', '.join(unsupported)}. Supported: {', '.join(sorted(self.SUPPORTED_METRICS))}"
            )

        self.metrics = normalized

    def evaluate(
        self,
        query: str,
        retrieved_chunks: list[Any],
        generated_answer: str | None = None,
        ground_truth: Any | None = None,
        trace: Any | None = None,
        **kwargs: Any,
    ) -> dict[str, float]:
        """Compute requested metrics for the given retrieval results.

        Args:
            query: The user query string.
            retrieved_chunks: Retrieved chunks or records.
            generated_answer: Optional generated answer (unused).
            ground_truth: Ground truth ids or structure.
            trace: Optional TraceContext (unused).
            **kwargs: Additional parameters (unused).

        Returns:
            Dictionary of metric name to float value.
        """
        self.validate_query(query)
        self._validate_retrieved_chunks_shape(retrieved_chunks)

        results: dict[str, float] = {}

        if "hit_rate" in self.metrics or "mrr" in self.metrics:
            retrieved_values: list[str] = []
            ground_truth_ids = self._extract_ground_truth_ids(ground_truth)
            if ground_truth_ids:
                ground_truth_values = ground_truth_ids
                match_mode = "id"
                if retrieved_chunks:
                    retrieved_values = self._extract_ids(
                        retrieved_chunks, label="retrieved_chunks",
                    )
            else:
                ground_truth_values = self._extract_ground_truth_sources(ground_truth)
                match_mode = "source"
                if ground_truth_values and retrieved_chunks:
                    retrieved_values = self._extract_sources(
                        retrieved_chunks, label="retrieved_chunks",
                    )

            if "hit_rate" in self.metrics:
                results["hit_rate"] = self._compute_hit_rate(
                    retrieved_values, ground_truth_values, match_mode=match_mode,
                )
            if "mrr" in self.metrics:
                results["mrr"] = self._compute_mrr(
                    retrieved_values, ground_truth_values, match_mode=match_mode,
                )
        if "faithfulness" in self.metrics:
            results["faithfulness"] = self._compute_faithfulness(
                generated_answer=generated_answer,
                retrieved_chunks=retrieved_chunks,
            )
        if "answer_similarity" in self.metrics:
            results["answer_similarity"] = self._compute_answer_similarity(
                generated_answer=generated_answer,
                reference_answer=self._extract_reference_answer(ground_truth),
            )

        return results

    def _metrics_from_settings(self, settings: Any) -> list[str]:
        """Extract metrics list from settings if available."""
        if settings is None:
            return []
        metrics = getattr(getattr(settings, "evaluation", None), "metrics", None)
        if metrics is None:
            return []
        return [str(metric) for metric in metrics]

    def _extract_ground_truth_ids(self, ground_truth: Any | None) -> list[str]:
        """Extract ground truth ids from various input shapes."""
        if ground_truth is None:
            return []
        if isinstance(ground_truth, str):
            return [ground_truth]
        if isinstance(ground_truth, dict):
            if "ids" in ground_truth and isinstance(ground_truth["ids"], list):
                return self._extract_ids(ground_truth["ids"], label="ground_truth.ids")
            if "reference_answer" in ground_truth and not any(
                field in ground_truth for field in self._ID_FIELDS
            ):
                return []
            return self._extract_ids([ground_truth], label="ground_truth")
        if isinstance(ground_truth, list):
            return self._extract_ids(ground_truth, label="ground_truth")

        raise ValueError(
            f"Unsupported ground_truth type: {type(ground_truth).__name__}. "
            "Expected str, dict, list, or None."
        )

    def _extract_ground_truth_sources(self, ground_truth: Any | None) -> list[str]:
        """Extract ground truth source names/paths from supported shapes."""
        if ground_truth is None:
            return []
        if isinstance(ground_truth, dict):
            sources = ground_truth.get("sources", [])
            if isinstance(sources, str):
                return [sources]
            if isinstance(sources, list):
                return [str(source) for source in sources]
        return []

    def _extract_reference_answer(self, ground_truth: Any | None) -> str | None:
        """Extract reference answer text from supported ground truth shapes."""
        if isinstance(ground_truth, dict):
            reference = ground_truth.get("reference_answer")
            if isinstance(reference, str) and reference.strip():
                return reference
        return None

    def _extract_ids(self, items: Iterable[Any], label: str) -> list[str]:
        """Extract ids from a list of items."""
        ids: list[str] = []
        for index, item in enumerate(items):
            if isinstance(item, str):
                ids.append(item)
                continue
            if isinstance(item, dict):
                for field in self._ID_FIELDS:
                    if field in item:
                        ids.append(str(item[field]))
                        break
                else:
                    raise ValueError(
                        f"Missing id field in {label}[{index}]. "
                        f"Expected one of {', '.join(self._ID_FIELDS)}"
                    )
                continue
            if hasattr(item, "id"):
                ids.append(str(getattr(item, "id")))
                continue

            raise ValueError(
                f"Unable to extract id from {label}[{index}] of type "
                f"{type(item).__name__}"
            )

        return ids

    def _extract_sources(self, items: Iterable[Any], label: str) -> list[str]:
        """Extract source paths from chunks or retrieval results."""
        sources: list[str] = []
        for index, item in enumerate(items):
            metadata = self._get_metadata(item)
            for field in self._SOURCE_FIELDS:
                if field in metadata and metadata[field]:
                    sources.append(str(metadata[field]))
                    break
            else:
                raise ValueError(
                    f"Missing source field in {label}[{index}]. "
                    f"Expected metadata with one of {', '.join(self._SOURCE_FIELDS)}"
                )
        return sources

    def _get_metadata(self, item: Any) -> dict[str, Any]:
        """Return a metadata dictionary from common chunk/result shapes."""
        if isinstance(item, dict):
            metadata = item.get("metadata")
            if isinstance(metadata, dict):
                return metadata
            return item
        metadata = getattr(item, "metadata", None)
        if isinstance(metadata, dict):
            return metadata
        return {}

    def _validate_retrieved_chunks_shape(self, retrieved_chunks: list[Any]) -> None:
        """Validate retrieved_chunks as a list while allowing empty retrieval results."""
        if not isinstance(retrieved_chunks, list):
            raise ValueError("retrieved_chunks must be a list")

    def _compute_hit_rate(
        self,
        retrieved_ids: Sequence[str],
        ground_truth_ids: Sequence[str],
        match_mode: str = "id",
    ) -> float:
        """Compute hit rate (binary)."""
        if not ground_truth_ids:
            return 0.0
        return (
            1.0
            if any(self._matches(item, ground_truth_ids, match_mode) for item in retrieved_ids)
            else 0.0
        )

    def _compute_mrr(
        self,
        retrieved_ids: Sequence[str],
        ground_truth_ids: Sequence[str],
        match_mode: str = "id",
    ) -> float:
        """Compute Mean Reciprocal Rank (MRR)."""
        if not ground_truth_ids:
            return 0.0
        for rank, item in enumerate(retrieved_ids, start=1):
            if self._matches(item, ground_truth_ids, match_mode):
                return 1.0 / rank
        return 0.0

    def _matches(self, item: str, expected: Sequence[str], match_mode: str) -> bool:
        """Check an item against expected values."""
        if match_mode == "source":
            item_path = Path(item)
            item_name = item_path.name
            return any(
                item == target
                or item_name == Path(target).name
                or target in item
                for target in expected
            )
        return item in expected

    def _compute_faithfulness(
        self,
        generated_answer: str | None,
        retrieved_chunks: Sequence[Any],
    ) -> float:
        """Compute a deterministic context-support proxy for faithfulness.

        This is intentionally lightweight: it measures how many answer tokens
        are present in the retrieved context. For LLM-as-judge faithfulness, use
        the Ragas evaluator instead.
        """
        answer_tokens = self._token_counts(generated_answer or "")
        if not answer_tokens:
            return 0.0

        context_text = " ".join(self._extract_text(chunk) for chunk in retrieved_chunks)
        context_tokens = self._token_counts(context_text)
        if not context_tokens:
            return 0.0

        supported = sum(
            min(count, context_tokens.get(token, 0))
            for token, count in answer_tokens.items()
        )
        total = sum(answer_tokens.values())
        return supported / total if total else 0.0

    def _compute_answer_similarity(
        self,
        generated_answer: str | None,
        reference_answer: str | None,
    ) -> float:
        """Compute token-overlap F1 between generated and reference answers."""
        generated_tokens = self._token_counts(generated_answer or "")
        reference_tokens = self._token_counts(reference_answer or "")
        if not generated_tokens or not reference_tokens:
            return 0.0

        overlap = sum(
            min(count, reference_tokens.get(token, 0))
            for token, count in generated_tokens.items()
        )
        precision = overlap / sum(generated_tokens.values())
        recall = overlap / sum(reference_tokens.values())
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)

    def _extract_text(self, item: Any) -> str:
        """Extract text content from common chunk/result shapes."""
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            return str(item.get("text", ""))
        if hasattr(item, "text"):
            return str(getattr(item, "text"))
        return str(item)

    def _token_counts(self, text: str) -> Counter[str]:
        """Tokenize English words/numbers and Chinese characters for overlap metrics."""
        tokens = re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text.lower())
        return Counter(tokens)
