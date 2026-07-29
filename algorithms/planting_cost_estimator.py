# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsField,
    QgsFeature,
    QgsFields
)
from qgis.PyQt.QtCore import QVariant
from .base_algorithm import BasePlantationAlgorithm

class PlantingCostEstimator(BasePlantationAlgorithm):
    P_IN_POLY = 'IN_POLY'
    P_SPH = 'SPH'
    P_COST_BIBIT = 'COST_BIBIT'
    P_COST_LC = 'COST_LC'
    P_COST_PUPUK = 'COST_PUPUK'
    P_OUT_POLY = 'OUT_POLY'

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'plantingcostestimator'

    def displayName(self):
        return '10. Planting Cost Estimator (Estimasi Biaya Tanam)'

    def group(self):
        return "03. Agronomy & Planting"

    def groupId(self):
        return 'agronomy'

    def createInstance(self):
        return PlantingCostEstimator()

    def shortHelpString(self):
        return "Menghitung estimasi biaya tanam dan menghasilkan layer baru berisi informasi biaya per blok (Poligon) untuk keperluan simulasi."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_IN_POLY,
            'Input Block/Area (Polygon)',
            types=[QgsProcessing.TypeVectorPolygon]
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_SPH,
            'Stand Per Hectare (SPH) - Trees/Ha',
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=136
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_COST_BIBIT,
            'Harga Bibit (Rp/Batang)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=45000
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_COST_LC,
            'Biaya Land Clearing (Rp/Ha)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=5500000
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_COST_PUPUK,
            'Biaya Pupuk Dasar (Rp/Batang)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=12500
        ))

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUT_POLY,
            'Estimasi Biaya Tanam (Layer Baru)',
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