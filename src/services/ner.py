"""Named Entity Recognition service using GLiNER with non-blocking execution."""

import asyncio
from typing import Any, Dict, List, Optional

from gliner import GLiNER

from src.config import settings
from src.utils.logging import logger


class GlinerNerService:
    """Service wrapping GLiNER multitask entity prediction."""

    def __init__(
        self,
        model_name: str = settings.gliner_model_name,
        default_labels: Optional[List[str]] = None,
        default_threshold: float = settings.ner_threshold,
    ) -> None:
        self.model_name = model_name
        self.default_labels = default_labels or list(settings.ner_labels)
        self.default_threshold = default_threshold
        self._model: Optional[GLiNER] = None

    def _load_model(self) -> GLiNER:
        """Load pretrained GLiNER model synchronously (cached)."""
        if self._model is None:
            logger.info("Loading GLiNER model '{}'...", self.model_name)
            self._model = GLiNER.from_pretrained(self.model_name)
            logger.info("GLiNER model loaded successfully.")
        return self._model

    async def ensure_model_loaded(self) -> None:
        """Asynchronously warm up and load model weights in a worker thread."""
        if self._model is None:
            await asyncio.to_thread(self._load_model)

    def _predict_sync(
        self,
        text: str,
        labels: List[str],
        threshold: float,
    ) -> List[Dict[str, Any]]:
        """Execute synchronous model inference."""
        model = self._load_model()
        return model.predict_entities(text, labels, threshold=threshold)

    async def extract_entities(
        self,
        text: str,
        labels: Optional[List[str]] = None,
        threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform named entity recognition on text within a separate worker thread.

        Returns list of entity dictionaries:
            [{"start": int, "end": int, "text": str, "label": str, "score": float}]
        """
        if not text or not text.strip():
            return []

        active_labels = labels if labels is not None else self.default_labels
        active_threshold = threshold if threshold is not None else self.default_threshold

        logger.debug(
            "Running GLiNER entity recognition on {} chars with labels {} and threshold {}",
            len(text),
            active_labels,
            active_threshold,
        )

        entities = await asyncio.to_thread(
            self._predict_sync,
            text,
            active_labels,
            active_threshold,
        )

        logger.debug("GLiNER discovered {} raw entity mentions", len(entities))
        return entities
