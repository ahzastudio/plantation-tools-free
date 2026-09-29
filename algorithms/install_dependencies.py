# -*- coding: utf-8 -*-

import os
import sys
import subprocess  # nosec B404
from qgis.core import (
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsMessageLog,
    Qgis
)
from .base_algorithm import BasePlantationAlgorithm

class InstallDependencies(BasePlantationAlgorithm):

    def get_minimum_tier(self):
        return "basic" # Basic tier karena ini utilitas sistem

    def name(self):
        return 'installdependencies'

    def displayName(self):
        return '00c. Install / Repair Dependencies'

    def group(self):
        return '00. System & Licensing'

    def groupId(self):
        return 'system'

    def createInstance(self):
        return InstallDependencies()

    def shortHelpString(self):
        return "Installs missing Python libraries required by advanced tools (like AI & Deep Learning) directly into QGIS."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterBoolean(
            'CONFIRM',
            'Saya mengerti alat ini akan mengunduh file dari internet (Memerlukan koneksi aktif)',
            defaultValue=True
        ))

    def processAlgorithm(self, parameters, context, feedback):
        from qgis.core import QgsProcessingException
        try:
            import qgis.utils
            from ..license_guard import LicenseDashboardDialog
            parent = qgis.utils.iface.mainWindow() if qgis.utils.iface else None
            dlg = LicenseDashboardDialog(parent, error_msg='FITUR PRO: Ini adalah versi Community/Free Edition. Silakan klik tombol di bawah untuk aktivasi/upgrade ke PRO.')
            if hasattr(dlg, 'exec'): dlg.exec()
            else: dlg.exec_()
        except Exception as e:
            import qgis.core
            qgis.core.QgsMessageLog.logMessage('License Check Error: ' + str(e), 'PlantationTools', qgis.core.Qgis.Warning)
        raise QgsProcessingException('FITUR PRO: Ini adalah versi Community/Free Edition. Silakan hubungi Admin via WhatsApp (+62 822-5476-0769) atau link wa.me/6282254760769 untuk Klaim Trial 14-Hari.')