# -*- coding: utf-8 -*-

import os
import tempfile
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsProcessingException,
    QgsWkbTypes,
    QgsVectorLayer,
    QgsFeatureSink,
    QgsCoordinateReferenceSystem,
    QgsProcessingMultiStepFeedback,
    QgsField
)
from qgis.PyQt.QtCore import QVariant
from .base_algorithm import BasePlantationAlgorithm
import processing

class OptimalRoadRouting(BasePlantationAlgorithm):
    P_START = 'START_POINT'
    P_END = 'END_POINT'
    P_DEM = 'INPUT_DEM'
    P_ROAD = 'EXISTING_ROAD'
    P_SLOPE_WEIGHT = 'SLOPE_WEIGHT'
    P_OFFROAD_COST = 'OFFROAD_COST'
    P_OUTPUT = 'OUTPUT'

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'optimalroadrouting'

    def displayName(self):
        return '25. Optimal Road Routing (Analisis Jalur Jalan Optimal)'

    def group(self):
        return '07. Analisa Infrastruktur (Jalan & Parit)'

    def groupId(self):
        return 'infra_analysis'

    def createInstance(self):
        return OptimalRoadRouting()

    def shortHelpString(self):
        return "Menemukan jalur paling efisien (Cost Path) dari titik awal ke titik tujuan dengan mempertimbangkan kemiringan (slope) dari DEM dan memanfaatkan jaringan jalan yang sudah ada."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_START, 'Start Point (Titik Awal)', types=[QgsProcessing.TypeVectorPoint]
        ))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_END, 'Destination Point (Titik Tujuan)', types=[QgsProcessing.TypeVectorPoint]
        ))
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.P_DEM, 'DEM Layer (Elevasi)'
        ))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_ROAD, 'Existing Road Network (Jaringan Jalan Awal) [Opsional]',
            types=[QgsProcessing.TypeVectorLine], optional=True
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.P_SLOPE_WEIGHT, 'Slope Weight (Bobot Kemiringan)',
            type=QgsProcessingParameterNumber.Double, defaultValue=1.0
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.P_OFFROAD_COST, 'Off-Road Cost Factor (Faktor Biaya Off-Road)',
            type=QgsProcessingParameterNumber.Double, defaultValue=10.0
        ))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUTPUT, 'Output Optimal Route (Jalur Optimal)', type=QgsProcessing.TypeVectorLine
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