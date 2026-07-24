# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterFileDestination,
    QgsProcessingException,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsField,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsVectorFileWriter,
    QgsWkbTypes
)
from qgis.PyQt.QtCore import QVariant
import os
import random
import numpy as np

try:
    from osgeo import gdal, osr
except ImportError:
    pass

from .base_algorithm import BasePlantationAlgorithm

class GenerateDummyData(BasePlantationAlgorithm):
    P_FOLDER = 'TARGET_FOLDER'

    def get_minimum_tier(self):
        return "basic"

    def name(self):
        return 'generatedummydata'

    def displayName(self):
        return '99. Generate Dummy Data (All Tools)'

    def group(self):
        return '99. Testing & Utilities'

    def groupId(self):
        return 'testing_utilities'

    def createInstance(self):
        return GenerateDummyData()

    def shortHelpString(self):
        return "Membuat data spasial dummy (Blok 2x2, Jalan, Titik Panen, dan Raster DEM) untuk menguji alat-alat analisis Plantation Tools."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFileDestination(
            self.P_FOLDER, 
            'Target Output Folder (Pilih direktori/folder)', 
            fileFilter="Folder", 
            defaultValue=""
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