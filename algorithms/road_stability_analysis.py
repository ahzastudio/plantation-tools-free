# -*- coding: utf-8 -*-

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
    QgsProcessingMultiStepFeedback,
    QgsField
)
from qgis.PyQt.QtCore import QVariant
from .base_algorithm import BasePlantationAlgorithm
import processing

class RoadStabilityAnalysis(BasePlantationAlgorithm):
    P_ROADS = 'ROADS'
    P_DEM = 'DEM'
    P_SOIL = 'SOIL'
    P_RAIN = 'RAINFALL'
    P_OUTPUT = 'OUTPUT'

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'roadstabilityanalysis'

    def displayName(self):
        return '20. Road Stability Analysis (Analisis Risiko Jalan)'

    def group(self):
        return "05. Infrastructure & Logistics"

    def groupId(self):
        return 'infrastructure'

    def createInstance(self):
        return RoadStabilityAnalysis()

    def shortHelpString(self):
        return "Mengevaluasi risiko kerusakan jalan (erosi/longsor) dengan memotong jalan setiap 50m dan mengkalkulasi skoring berdasarkan kemiringan lereng (DEM) dan curah hujan."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_ROADS, 'Road Network (Jaringan Jalan)', types=[QgsProcessing.TypeVectorLine]
        ))
        
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.P_DEM, 'Elevation Model (DEM)'
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_SOIL, 'Soil Type (Poligon Tanah) [Opsional]', types=[QgsProcessing.TypeVectorPolygon], optional=True
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_RAIN, 'Annual Rainfall (Curah Hujan mm/thn) [Opsional]',
            type=QgsProcessingParameterNumber.Integer, defaultValue=2500
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUTPUT, 'Output Risk Map (Segmen Jalan)', type=QgsProcessing.TypeVectorLine
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