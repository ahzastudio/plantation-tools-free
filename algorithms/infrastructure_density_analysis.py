# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsWkbTypes,
    QgsFeatureSink,
    QgsFeature,
    QgsGeometry,
    QgsField,
    QgsFields,
    QgsProcessingMultiStepFeedback
)
from qgis.PyQt.QtCore import QVariant
import processing
from .base_algorithm import BasePlantationAlgorithm

class InfrastructureDensityAnalysis(BasePlantationAlgorithm):
    P_LINES = 'INPUT_LINES'
    P_BLOCKS = 'INPUT_BLOCKS'
    P_TYPE = 'INFRA_TYPE'
    P_OUTPUT = 'OUTPUT'
    
    INFRA_TYPES = [
        "Parit Tersier / Lapangan (Field Drain)",
        "Parit Sekunder / Pengumpul (Collection Drain)",
        "Parit Primer / Besar (Main Drain)",
        "Parit Outlet / Pembuang (Outlet Drain)",
        "Jalan Subsidiari / Pengumpul (Collection Road)",
        "Jalan Utama / Besar (Main Road)"
    ]

    def get_minimum_tier(self):
        return "basic"

    def name(self):
        return 'infrastructuredensity'

    def displayName(self):
        return '23. Kerapatan Infrastruktur (Jalan & Parit)'

    def group(self):
        return '07. Analisa Infrastruktur (Jalan & Parit)'

    def groupId(self):
        return 'infra_analysis'

    def createInstance(self):
        return InfrastructureDensityAnalysis()

    def shortHelpString(self):
        return "Menghitung kerapatan infrastruktur (m/ha) di setiap blok. Digunakan untuk evaluasi jalan dan parit perkebunan."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_LINES, 'Layer Infrastruktur (Garis Parit/Jalan)', types=[QgsProcessing.TypeVectorLine]
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_BLOCKS, 'Layer Blok (Poligon)', types=[QgsProcessing.TypeVectorPolygon]
        ))
        
        self.addParameter(QgsProcessingParameterEnum(
            self.P_TYPE, 'Jenis Infrastruktur',
            options=self.INFRA_TYPES,
            defaultValue=0
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUTPUT, 'Output Kerapatan Blok', type=QgsProcessing.TypeVectorPolygon
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