"""Tests for logis.core.progress module."""

from logis.core.progress import NullProgress, PhaseProgress, phase


class DummyFeedback:
    """Mock feedback object recording calls and cancellation status."""

    def __init__(self, canceled: bool = False):
        self.progress_history = []
        self.info_history = []
        self.warning_history = []
        self.text_history = []
        self.canceled = canceled

    def setProgress(self, progress: float) -> None:
        self.progress_history.append(progress)

    def setProgressText(self, text: str) -> None:
        self.text_history.append(text)

    def pushInfo(self, info: str) -> None:
        self.info_history.append(info)

    def pushWarning(self, warning: str) -> None:
        self.warning_history.append(warning)

    def isCanceled(self) -> bool:
        return self.canceled


def test_phase_progress_mapping():
    """Test that range maps 0 -> start, 100 -> end, 50 -> middle."""
    fb = DummyFeedback()
    prog = PhaseProgress(fb, start=20.0, end=80.0)

    prog.setProgress(0)
    assert fb.progress_history[-1] == 20.0

    prog.setProgress(100)
    assert fb.progress_history[-1] == 80.0

    prog.setProgress(50)
    assert fb.progress_history[-1] == 50.0


def test_phase_progress_clamping():
    """Test that values outside 0-100 range are clamped."""
    fb = DummyFeedback()
    prog = PhaseProgress(fb, start=10.0, end=90.0)

    prog.setProgress(-25)
    assert fb.progress_history[-1] == 10.0

    prog.setProgress(150)
    assert fb.progress_history[-1] == 90.0


def test_is_canceled_propagation():
    """Test that isCanceled propagates from dummy feedback."""
    fb = DummyFeedback(canceled=False)
    prog = PhaseProgress(fb, start=0, end=100)
    assert prog.isCanceled() is False

    fb.canceled = True
    assert prog.isCanceled() is True


def test_nested_phases():
    """Test that nested sub-ranges compose correctly."""
    fb = DummyFeedback()
    parent = PhaseProgress(fb, start=0.0, end=50.0)
    child = phase(parent, start=0.0, end=50.0)

    child.setProgress(0)
    assert fb.progress_history[-1] == 0.0

    child.setProgress(100)
    assert fb.progress_history[-1] == 25.0

    child.setProgress(50)
    assert fb.progress_history[-1] == 12.5


def test_feedback_none_and_null_progress():
    """Test that feedback=None does not crash and returns False for isCanceled()."""
    prog_none = PhaseProgress(None, start=0.0, end=100.0)
    assert isinstance(prog_none, NullProgress)
    prog_none.setProgress(50)
    prog_none.setProgressText("test text")
    prog_none.pushInfo("test")
    prog_none.pushWarning("test warning")
    assert prog_none.isCanceled() is False

    shortcut_none = phase(None, 10.0, 90.0)
    assert isinstance(shortcut_none, NullProgress)
    assert shortcut_none.isCanceled() is False

    null_prog = NullProgress()
    null_prog.setProgress(50)
    null_prog.setProgressText("text")
    null_prog.pushInfo("info")
    null_prog.pushWarning("warn")
    assert null_prog.isCanceled() is False


def test_push_info_and_warning_delegation():
    """Test that pushInfo, pushWarning and setProgressText delegate to underlying feedback."""
    fb = DummyFeedback()
    prog = PhaseProgress(fb, start=0, end=100)

    prog.pushInfo("Info message")
    assert fb.info_history == ["Info message"]

    prog.pushWarning("Warning message")
    assert fb.warning_history == ["Warning message"]

    prog.setProgressText("Text message")
    assert fb.text_history == ["Text message"]
