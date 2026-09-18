"""
extractors/base.py — Abstract base class for all data extractors.

Every extractor in this pipeline must inherit from BaseExtractor and
implement the `extract()` method. This enforces a consistent interface
across all data sources (Stripe, Salesforce, databases, etc.).

Design notes:
  - BaseExtractor is a generic class: `BaseExtractor[T]` where T is the
    Pydantic model the extractor returns a list of.
  - Subclasses set `source_name` for logging and manifest metadata.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Generic, List, Tuple, TypeVar

from utils.logger import get_logger

# T is the Pydantic model type (e.g. Customer)
T = TypeVar("T")


class BaseExtractor(ABC, Generic[T]):
    """
    Abstract base for all ETL extractors.

    Subclasses must implement:
        source_name (str): Human-readable name of the data source.
        extract()   : Fetch all records and return List[T].
    """

    #: Override in subclasses. Used in logs and S3 manifest metadata.
    source_name: str = "unknown"

    def __init__(self) -> None:
        self.logger = get_logger(f"etl.extractor.{self.source_name}")

    @abstractmethod
    def extract(self) -> List[T]:
        """
        Fetch all records from the data source.

        Returns:
            A list of validated Pydantic model instances.

        Raises:
            Any exception propagates up to the pipeline orchestrator.
        """
        ...

    def extract_with_timing(self) -> Tuple[List[T], float]:
        """
        Convenience wrapper that times the `extract()` call.

        Returns:
            Tuple of (records, elapsed_seconds).
        """
        start = time.perf_counter()
        records = self.extract()
        elapsed = round(time.perf_counter() - start, 3)
        self.logger.info(
            "Extraction complete",
            extra={
                "source": self.source_name,
                "record_count": len(records),
                "elapsed_seconds": elapsed,
            },
        )
        return records, elapsed
