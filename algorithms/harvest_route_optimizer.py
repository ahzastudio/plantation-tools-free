# -*- coding: utf-8 -*-

import os
import uuid
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsWkbTypes,
    QgsProcessingUtils,
    QgsVectorLayer,
    QgsFeatureSink,
    QgsFeatureRequest,
    QgsProcessingMultiStepFeedback
)
from qgis.PyQt.QtCore import QVariant
from .base_algorithm import BasePlantationAlgorithm
import processing

class HarvestRouteOptimizer(BasePlantationAlgorithm):
    P_SOURCE = 'SOURCE_POINTS'
    P_DEST = 'DEST_POINT'
    P_ROADS = 'ROADS'
    P_DEM = 'DEM'
    P_OUTPUT = 'OUTPUT_ROUTES'

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'harvestrouteoptimizer'

    def displayName(self):
        return '19. Harvest Route Optimizer (Optimasi Rute Panen)'

    def group(self):
        return '05. Infrastructure & Logistics'

    def groupId(self):
        return 'infrastructure'

    def createInstance(self):
        return HarvestRouteOptimizer()

    def shortHelpString(self):
        return "Mengkalkulasi rute terdekat dan paling efisien dari titik panen (blok) menuju pabrik (PKS/TPA) mempertimbangkan jalan dan topografi."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_SOURCE, 'Harvest Points (Titik Panen)', types=[QgsProcessing.TypeVectorPoint]
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_DEST, 'Target Factory / Dump (Pabrik)', types=[QgsProcessing.TypeVectorPoint]
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_ROADS, 'Road Network (Jaringan Jalan) [Opsional]', types=[QgsProcessing.TypeVectorLine], optional=True
        ))
        
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.P_DEM, 'Elevation Model (DEM) [Opsional]', optional=True
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUTPUT, 'Output Routes (Rute Optimal)', type=QgsProcessing.TypeVectorLine
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