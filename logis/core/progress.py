"""Progress reporting utilities for sub-phases of execution.

This module is pure stdlib (no QGIS dependency allowed).
The progress objects (`NullProgress`, `PhaseProgress`) are intentionally
duck-typed with `QgsProcessingFeedback` so they can be passed directly to
functions expecting feedback objects, such as `build_graph` or `compute_od_matrix`.
"""

from typing import Any, Optional


class NullProgress:
    """No-op progress tracker duck-typed with QgsProcessingFeedback."""

    def setProgress(self, progress: float) -> None:
        """Do nothing."""
        pass

    def setProgressText(self, text: str) -> None:
        """Do nothing."""
        pass

    def pushInfo(self, info: str) -> None:
        """Do nothing."""
        pass

    def pushWarning(self, warning: str) -> None:
        """Do nothing."""
        pass

    def isCanceled(self) -> bool:
        """Always return False."""
        return False


class PhaseProgress:
    """Sub-phase progress wrapper duck-typed with QgsProcessingFeedback.

    Maps progress values from 0.0..100.0 to a sub-range [start, end] of parent feedback.
    """

    def __new__(
        cls,
        feedback: Optional[Any] = None,
        start: float = 0.0,
        end: float = 100.0,
    ) -> Any:
        if feedback is None:
            return NullProgress()
        return super().__new__(cls)

    def __init__(
        self,
        feedback: Optional[Any] = None,
        start: float = 0.0,
        end: float = 100.0,
    ) -> None:
        self._feedback = feedback
        self._start = float(start)
        self._end = float(end)

    def setProgress(self, progress: float) -> None:
        """Set progress mapped into [start, end] sub-range."""
        p = max(0.0, min(100.0, float(progress)))
        mapped = self._start + (self._end - self._start) * p / 100.0
        if hasattr(self._feedback, "setProgress"):
            self._feedback.setProgress(mapped)

    def setProgressText(self, text: str) -> None:
        """Delegate setProgressText call to parent feedback."""
        if hasattr(self._feedback, "setProgressText"):
            self._feedback.setProgressText(text)

    def pushInfo(self, info: str) -> None:
        """Delegate pushInfo call to parent feedback."""
        if hasattr(self._feedback, "pushInfo"):
            self._feedback.pushInfo(info)

    def pushWarning(self, warning: str) -> None:
        """Delegate pushWarning call to parent feedback."""
        if hasattr(self._feedback, "pushWarning"):
            self._feedback.pushWarning(warning)

    def isCanceled(self) -> bool:
        """Delegate isCanceled call to parent feedback, defaulting to False."""
        if hasattr(self._feedback, "isCanceled"):
            return bool(self._feedback.isCanceled())
        return False


def phase(
    feedback: Optional[Any] = None,
    start: float = 0.0,
    end: float = 100.0,
) -> Any:
    """Shortcut function to create a PhaseProgress object."""
    return PhaseProgress(feedback, start, end)
