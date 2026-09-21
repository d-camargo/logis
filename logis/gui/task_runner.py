from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.core import (
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProject,
    QgsApplication,
    QgsProcessingAlgRunnerTask,
)
import processing


class SignalFeedback(QgsProcessingFeedback, QObject):
    message_emitted = pyqtSignal(str)

    def __init__(self):
        QgsProcessingFeedback.__init__(self)
        QObject.__init__(self)

    def pushInfo(self, info: str):
        self.message_emitted.emit(info)
        super().pushInfo(info)

    def pushWarning(self, warning: str):
        self.message_emitted.emit(warning)
        super().pushWarning(warning)


class AlgTaskRunner:
    def __init__(self, alg_id, params, on_finished, on_message=None, on_progress=None):
        self.alg_id = alg_id
        self.params = params
        self.on_finished = on_finished

        self.context = QgsProcessingContext()
        self.context.setProject(QgsProject.instance())

        self.feedback = SignalFeedback()
        if on_message:
            self.feedback.message_emitted.connect(on_message)
        if on_progress:
            self.feedback.progressChanged.connect(on_progress)

        self.task = None

    def start(self):
        if not hasattr(QgsApplication, 'taskManager') or QgsApplication.taskManager() is None:
            results = processing.run(
                self.alg_id,
                self.params,
                context=self.context,
                feedback=self.feedback
            )
            self.on_finished(True, results)
            return

        self.task = QgsProcessingAlgRunnerTask(self.alg_id, self.params, self.context, self.feedback)
        self.task.executed.connect(self.on_finished)
        QgsApplication.taskManager().addTask(self.task)

    def cancel(self):
        self.feedback.cancel()

    def resolve_layer(self, results, chave):
        if not results or chave not in results:
            return None

        value = results[chave]
        if isinstance(value, str):
            layer = self.context.takeResultLayer(value)
            if layer:
                return layer
        return value
