# -*- coding: utf-8 -*-
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterEnum,
    QgsProcessingParameterRasterDestination,
    QgsProcessingException
)
from qgis import processing
from .base_algorithm import BasePlantationAlgorithm

class SoilMoistureAnalysis(BasePlantationAlgorithm):
    P_IN_RASTER = 'IN_RASTER'
    P_METHOD = 'METHOD'
    P_OUT_RASTER = 'OUT_RASTER'

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'soilmoistureanalysis'

    def displayName(self):
        return '17. Soil Moisture Analysis (Kelembapan Tanah)'

    def group(self):
        return "03. Agronomy & Planting"

    def groupId(self):
        return 'agronomy'

    def shortHelpString(self):
        return (
            "Menganalisis kelembapan tanah menggunakan TWI (Topographic Wetness Index) dari DEM "
            "atau NDWI dari citra multispektral.\n\n"
            "TWI dihitung secara native tanpa perlu instalasi SAGA — "
            "menggunakan rumus: TWI = ln(1 / tan(kemiringan))."
        )

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.P_IN_RASTER, 'Input Raster (DEM / Multispectral)'
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.P_METHOD, 'Analysis Method',
                options=['TWI (Topographic Wetness Index - DEM)', 'NDWI (Multispectral)'],
                defaultValue=0
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.P_OUT_RASTER, 'Output Moisture Raster'
            )
        )

    def createInstance(self):
        return SoilMoistureAnalysis()

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