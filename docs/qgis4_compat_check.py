#!/usr/bin/env python3
"""qgis4_compat_check.py - Relatório de compatibilidade QGIS 4 / Qt6 vs QGIS 3 / Qt5.

Pode ser executado via CLI (`python3 docs/qgis4_compat_check.py`) ou colado
diretamente no console Python do QGIS.
"""

import sys

# Importações seguras de módulos PyQGIS / PyQt
try:
    from qgis.core import Qgis
except Exception:
    Qgis = None

try:
    from qgis.PyQt.QtCore import QT_VERSION_STR, PYQT_VERSION_STR, Qt, QMetaType, QVariant
    from qgis.PyQt.QtWidgets import QDialog
except Exception:
    try:
        from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR, Qt, QMetaType, QVariant
        from PyQt5.QtWidgets import QDialog
    except Exception:
        try:
            from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR, Qt, QMetaType
            from PyQt6.QtWidgets import QDialog
            QVariant = None
        except Exception:
            QT_VERSION_STR = "N/A"
            PYQT_VERSION_STR = "N/A"
            Qt = None
            QMetaType = None
            QVariant = None
            QDialog = None

try:
    from qgis.core import (
        QgsWkbTypes,
        QgsProcessing,
        QgsProcessingParameterNumber,
        QgsTask,
        QgsField,
    )
except Exception:
    QgsWkbTypes = None
    QgsProcessing = None
    QgsProcessingParameterNumber = None
    QgsTask = None
    QgsField = None


def check_attr(obj, attr_path):
    if obj is None:
        return False
    current = obj
    for part in attr_path.split('.'):
        if not hasattr(current, part):
            return False
        current = getattr(current, part)
    return current is not None


def check_qgs_field_qmetatype():
    if QgsField is None or QMetaType is None:
        return False
    try:
        tp = getattr(getattr(QMetaType, 'Type', None), 'QString', None)
        if tp is None:
            return False
        _ = QgsField("t", tp)
        return True
    except Exception:
        return False


def run_compat_check():
    qgis_ver = getattr(Qgis, 'QGIS_VERSION', 'N/A') if Qgis else 'N/A'
    qt_ver = QT_VERSION_STR if 'QT_VERSION_STR' in globals() else 'N/A'
    pyqt_ver = PYQT_VERSION_STR if 'PYQT_VERSION_STR' in globals() else 'N/A'

    print("=== RELATÓRIO DE COMPATIBILIDADE QGIS 4 / QT6 ===")
    print(f"QGIS Version: {qgis_ver}")
    print(f"Qt Version:   {qt_ver}")
    print(f"PyQt Version: {pyqt_ver}")
    print("-" * 50)

    checks = [
        ("Qt.RightDockWidgetArea", Qt, "RightDockWidgetArea"),
        ("Qt.DockWidgetArea.RightDockWidgetArea", Qt, "DockWidgetArea.RightDockWidgetArea"),
        ("QVariant.String", QVariant, "String"),
        ("QMetaType.Type.QString", QMetaType, "Type.QString"),
        ("QgsWkbTypes.LineString", QgsWkbTypes, "LineString"),
        ("QgsWkbTypes.Type.LineString", QgsWkbTypes, "Type.LineString"),
        ("QgsProcessing.TypeVectorLine", QgsProcessing, "TypeVectorLine"),
        ("QgsProcessing.SourceType.TypeVectorLine", QgsProcessing, "SourceType.TypeVectorLine"),
        ("QgsProcessingParameterNumber.Double", QgsProcessingParameterNumber, "Double"),
        ("QgsProcessingParameterNumber.Type.Double", QgsProcessingParameterNumber, "Type.Double"),
        ("QgsTask.CanCancel", QgsTask, "CanCancel"),
        ("QgsTask.Flag.CanCancel", QgsTask, "Flag.CanCancel"),
        ("QDialog.exec_", QDialog, "exec_"),
        ("QDialog.exec", QDialog, "exec"),
    ]

    for label, base_obj, path in checks:
        status = "OK" if check_attr(base_obj, path) else "AUSENTE"
        print(f"{status:<8} {label}")

    field_status = "OK" if check_qgs_field_qmetatype() else "AUSENTE"
    print(f"{field_status:<8} QgsField(\"t\", QMetaType.Type.QString)")
    print("=" * 50)


if __name__ == "__main__":
    run_compat_check()
