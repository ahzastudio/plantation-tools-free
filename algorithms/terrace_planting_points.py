# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsFeatureSink,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsWkbTypes,
    QgsPointXY,
    QgsGeometry,
    QgsSpatialIndex
)
from qgis.PyQt.QtCore import QVariant
import math
import os
from .base_algorithm import BasePlantationAlgorithm

class TerracePlantingPoints(BasePlantationAlgorithm):
    P_IN_LINES = 'IN_LINES'
    P_PATTERN = 'PATTERN'
    P_LR_SPACING = 'LR_SPACING'
    P_TOLERANCE = 'TOLERANCE'
    P_MARGIN = 'MARGIN'
    P_LONG_SPACING = 'LONG_SPACING'
    P_OUT_POINTS = 'OUT_POINTS'
    P_OUT_LINES = 'OUT_LINES'

    PATTERN_OPTS = ["CENTER_LINE", "SEGITIGA_MATA_GERGAJI"]

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'terraceplantingpoints'

    def displayName(self):
        return '07. Generate Terrace Points (Titik Tanam Teras)'

    def group(self):
        return "03. Agronomy & Planting"

    def groupId(self):
        return 'agronomy'

    def createInstance(self):
        return TerracePlantingPoints()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_IN_LINES,
            'Terrace Lines (Polyline)',
            types=[QgsProcessing.TypeVectorLine]
        ))

        self.addParameter(QgsProcessingParameterEnum(
            self.P_PATTERN,
            'Planting Pattern (Pola Tanam)',
            options=self.PATTERN_OPTS,
            defaultValue=0
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_LR_SPACING,
            'Left-Right Spacing (Jarak Kiri-Kanan) (m)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=6.0,
            optional=True
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_TOLERANCE,
            'Min. Distance / Tolerance (m)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=5.0,
            optional=True
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_MARGIN,
            'Margin from Edge (m)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=1.0
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_LONG_SPACING,
            'Longitudinal Spacing (Jarak Memanjang) (m)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=4.0
        ))

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUT_POINTS,
            'Output Planting Points',
            type=QgsProcessing.TypeVectorPoint
        ))

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUT_LINES,
            'Output Connecting Lines',
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