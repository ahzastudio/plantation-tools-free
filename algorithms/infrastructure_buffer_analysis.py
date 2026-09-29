# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsWkbTypes,
    QgsFeatureSink,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsProcessingMultiStepFeedback
)
from qgis.PyQt.QtCore import QVariant
import processing
from .base_algorithm import BasePlantationAlgorithm

class InfrastructureBufferAnalysis(BasePlantationAlgorithm):
    P_LINES = 'INPUT_LINES'
    P_TYPE = 'INFRA_TYPE'
    P_CUSTOM_WIDTH = 'CUSTOM_WIDTH'
    P_BLOCKS = 'INPUT_BLOCKS'
    P_OUTPUT = 'OUTPUT'
    
    # Konfigurasi dictionary untuk referensi lebar
    INFRA_SPECS = {
        0: {"nama": "Parit Tersier / Lapangan (Field Drain)", "lebar": 0.90},
        1: {"nama": "Parit Sekunder / Pengumpul (Collection Drain)", "lebar": 1.50},
        2: {"nama": "Parit Primer / Besar (Main Drain)", "lebar": 1.80},
        3: {"nama": "Parit Outlet / Pembuang (Outlet Drain)", "lebar": 2.40},
        4: {"nama": "Jalan Subsidiari / Pengumpul (Collection Road)", "lebar": 4.65},
        5: {"nama": "Jalan Utama / Besar (Main Road)", "lebar": 5.50}
    }

    def get_minimum_tier(self):
        return "basic"

    def name(self):
        return 'infrastructurebuffer'

    def displayName(self):
        return '24. Buffer & Luas Area Infrastruktur (Loss/Hilang)'

    def group(self):
        return '07. Analisa Infrastruktur (Jalan & Parit)'

    def groupId(self):
        return 'infra_analysis'

    def createInstance(self):
        return InfrastructureBufferAnalysis()

    def shortHelpString(self):
        return "Membuat zona buffer di sekitar jalan/parit dan memotongnya dengan batas blok untuk menghitung seberapa besar area tanam (HA) yang hilang akibat pembangunan infrastruktur tersebut."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_LINES, 'Layer Infrastruktur (Garis Parit/Jalan)', types=[QgsProcessing.TypeVectorLine]
        ))
        
        self.addParameter(QgsProcessingParameterEnum(
            self.P_TYPE, 'Jenis Infrastruktur',
            options=[spec["nama"] for spec in self.INFRA_SPECS.values()],
            defaultValue=0
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_CUSTOM_WIDTH, 'Lebar Kustom (M) [Kosongkan utk pakai standar]',
            type=QgsProcessingParameterNumber.Double,
            optional=True, defaultValue=None
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_BLOCKS, 'Clip ke Layer Blok (Opsional, untuk hitung area loss)', types=[QgsProcessing.TypeVectorPolygon],
            optional=True
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUTPUT, 'Output Buffer (Poligon)', type=QgsProcessing.TypeVectorPolygon
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