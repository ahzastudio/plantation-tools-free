# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsFeatureSink,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsWkbTypes,
    QgsSpatialIndex
)
from qgis.PyQt.QtCore import QVariant
from .base_algorithm import BasePlantationAlgorithm

class CalculateSPH(BasePlantationAlgorithm):
    P_IN_BLOCK = 'IN_BLOCK'
    P_IN_POINTS = 'IN_POINTS'
    P_OUT_BLOCK = 'OUT_BLOCK'

    def get_minimum_tier(self):
        return "basic"

    def name(self):
        return 'calculatesph'

    def displayName(self):
        return '12. Calculate SPH (Stand Per Hectare)'

    def group(self):
        return "03. Agronomy & Planting"

    def groupId(self):
        return 'agronomy'

    def createInstance(self):
        return CalculateSPH()

    def shortHelpString(self):
        return "Calculates densitas tanaman (Stand Per Hectare) per block by counting planting points within each block area."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_IN_BLOCK,
            'Input Block Layer (Polygon)',
            types=[QgsProcessing.TypeVectorPolygon]
        ))

        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_IN_POINTS,
            'Input Planting Points (Point)',
            types=[QgsProcessing.TypeVectorPoint]
        ))

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUT_BLOCK,
            'Updated Block Layer (With SPH)',
            type=QgsProcessing.TypeVectorPolygon
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