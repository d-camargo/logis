# -*- coding: utf-8 -*-
"""logis — QGIS plugin for logistics in Brazil.
"""


def classFactory(iface):
    import os
    from qgis.PyQt.QtCore import QCoreApplication, QTranslator, QSettings
    locale = (QSettings().value("locale/userLocale") or "en")[:2]
    qm = os.path.join(os.path.dirname(__file__), "i18n", f"logis_{locale}.qm")
    if os.path.exists(qm):
        translator = QTranslator()
        if translator.load(qm):
            QCoreApplication.installTranslator(translator)
            classFactory._translator = translator
    from .logis_plugin import LogisPlugin
    return LogisPlugin(iface)
