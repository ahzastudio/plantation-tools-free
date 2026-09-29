# -*- coding: utf-8 -*-

import math
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsField,
    QgsFeature,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsWkbTypes,
    QgsSpatialIndex
)
from qgis.PyQt.QtCore import QVariant
from .base_algorithm import BasePlantationAlgorithm

class PlantingDistanceAssessment(BasePlantationAlgorithm):
    P_IN_TREES = 'IN_TREES'
    P_SEARCH_RADIUS = 'SEARCH_RADIUS'
    P_MAX_NEIGHBORS = 'MAX_NEIGHBORS'
    P_OUT_LINES = 'OUT_LINES'

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'plantingdistanceassessment'

    def displayName(self):
        return '13. Planting Distance Assessment'

    def group(self):
        return '03. Agronomy & Planting'

    def groupId(self):
        return 'agronomy'

    def createInstance(self):
        return PlantingDistanceAssessment()

    def shortHelpString(self):
        return "Creates lines between neighboring trees to analyze planting distances (Triangulation)."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_IN_TREES,
            'Titik Tanam (Input Point)',
            types=[QgsProcessing.TypeVectorPoint]
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_SEARCH_RADIUS,
            'Radius Pencarian (Meter)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=12.0
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_MAX_NEIGHBORS,
            'Jumlah Tetangga Maksimal',
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=6
        ))

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUT_LINES,
            'Output Garis Jarak (Line)',
            type=QgsProcessing.TypeVectorLine
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