# -*- coding: utf-8 -*-
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsFeatureSink,
    QgsFeature,
    QgsGeometry,
    QgsWkbTypes
)
from .base_algorithm import BasePlantationAlgorithm
import math

class BlockCentroidRouting(BasePlantationAlgorithm):
    P_IN_BLOCKS = 'IN_BLOCKS'
    P_OUT_LINES = 'OUT_LINES'

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'blockcentroidrouting'

    def displayName(self):
        return '26. Block Centroid Routing (Kalkulator Jalan via Centroid)'

    def group(self):
        return '07. Analisa Infrastruktur (Jalan & Parit)'

    def groupId(self):
        return 'infra_analysis'

    def shortHelpString(self):
        return "Mengekstrak centroid dari blok dan membuat jaringan jalan."

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.P_IN_BLOCKS, 'Input Block Polygons', types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.P_OUT_LINES, 'Output Road Network (Lines)'
            )
        )

    def createInstance(self):
        return BlockCentroidRouting()

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