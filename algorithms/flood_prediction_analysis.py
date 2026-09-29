# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException
)
# pyrefly: ignore [missing-import]
from qgis import processing
from .base_algorithm import BasePlantationAlgorithm

class FloodPredictionAnalysis(BasePlantationAlgorithm):
    P_IN_DEM = 'IN_DEM'
    P_OUT_POLY = 'OUT_POLY'

    def get_minimum_tier(self):
        return "pro+"

    def name(self):
        return 'floodpredictionanalysis'

    def displayName(self):
        return '28. Flood Prediction Analysis (Prediksi Area Banjir)'

    def group(self):
        return '08. Analisa Lingkungan & NKT'

    def groupId(self):
        return 'environment_nkt'

    def shortHelpString(self):
        return "Memprediksi area rawan genangan banjir dengan mengkombinasikan Flow Accumulation dan Slope."

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.P_IN_DEM, 'Input DEM Raster'
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.P_OUT_POLY, 'Output Flood Risk Areas (Polygons)'
            )
        )

    def createInstance(self):
        return FloodPredictionAnalysis()

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