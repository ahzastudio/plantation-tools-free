# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException
)
# pyrefly: ignore [missing-import]
from qgis import processing
from .base_algorithm import BasePlantationAlgorithm

class DeteksiKlorosisPokok(BasePlantationAlgorithm):
    P_IN_POINTS = 'IN_POINTS'
    P_IN_RASTER = 'IN_RASTER'
    P_MODE = 'MODE'
    P_THRESHOLD = 'THRESHOLD'
    P_BUFFER_RAD = 'BUFFER_RAD'
    P_OUT_POINTS = 'OUT_POINTS'
    P_OUT_POLYGONS = 'OUT_POLYGONS'

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'deteksiklorosispokok'

    def displayName(self):
        return '16. Deteksi Klorosis Pokok (Hybrid)'

    def group(self):
        return '03. Agronomy & Planting'

    def groupId(self):
        return 'agronomy'

    def shortHelpString(self):
        return "Mendeteksi pokok sawit yang menguning (klorosis) dari citra UAV RGB atau Indeks Vegetasi (NDVI/GNDVI)."

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.P_IN_POINTS, 'Input Titik Pokok Sawit', [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.P_IN_RASTER, 'Input Raster (RGB / Indeks Vegetasi)'
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.P_MODE, 'Mode Deteksi Klorosis',
                options=['RGB (Mendeteksi warna kuning)', 'Index (Nilai piksel < Threshold)'],
                defaultValue=0
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_THRESHOLD, 'Threshold Indeks Vegetasi (Klorosis jika < X) [Default: 0.40]',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.40, optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_BUFFER_RAD, 'Radius Area Klorosis (Meter)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=4.5
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.P_OUT_POINTS, 'Output Titik Klorosis'
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.P_OUT_POLYGONS, 'Output Area Klorosis / Buffer'
            )
        )

    def createInstance(self):
        return DeteksiKlorosisPokok()

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