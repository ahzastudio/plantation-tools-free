# -*- coding: utf-8 -*-

import math
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsField,
    QgsFeature,
    QgsFields,
    QgsPointXY,
    QgsWkbTypes,
    QgsGeometry
)
from qgis.PyQt.QtCore import QVariant
from .base_algorithm import BasePlantationAlgorithm

class RoadCutFillAnalysis(BasePlantationAlgorithm):
    P_IN_ROAD = 'IN_ROAD'
    P_IN_DEM = 'IN_DEM'
    P_WIDTH = 'WIDTH'
    P_INTERVAL = 'INTERVAL'
    P_WINDOW = 'WINDOW'
    P_OUT_POINTS = 'OUT_POINTS'

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'roadcutfillanalysis'

    def displayName(self):
        return '13. Road Cut & Fill Analysis (Analisis Gali Timbun Jalan)'

    def group(self):
        return "03. Agronomy & Planting"

    def groupId(self):
        return 'agronomy'

    def createInstance(self):
        return RoadCutFillAnalysis()

    def shortHelpString(self):
        return "Estimates Cut & Fill volumes for road construction using DEM and Design Grade smoothing (Simple Moving Average)."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_IN_ROAD,
            'Input Road Centerline (Polyline)',
            types=[QgsProcessing.TypeVectorLine]
        ))
        
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.P_IN_DEM,
            'Input DEM (Raster)'
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_WIDTH,
            'Road Width (meter)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=6.0
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_INTERVAL,
            'Sampling Interval (meter)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=10.0
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_WINDOW,
            'Smoothing Window (points)',
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=5
        ))

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUT_POINTS,
            'Output Cut/Fill Points',
            type=QgsProcessing.TypeVectorPoint
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