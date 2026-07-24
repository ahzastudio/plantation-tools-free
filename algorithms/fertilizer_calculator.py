# -*- coding: utf-8 -*-

import math
import processing
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterEnum,
    QgsProcessingParameterString,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsField,
    QgsFeature,
    QgsFields,
    QgsVectorLayer
)
from qgis.PyQt.QtCore import QVariant
from .base_algorithm import BasePlantationAlgorithm

class FertilizerCalculator(BasePlantationAlgorithm):
    P_IN_BLOCK = 'IN_BLOCK'
    P_TREE_COUNT_FIELD = 'TREE_COUNT_FIELD'
    P_MODE = 'MODE'
    P_FERT_TYPE = 'FERT_TYPE'
    P_DOSAGE = 'DOSAGE'
    P_FREQ = 'FREQ'
    
    P_LOW_DOSAGE = 'LOW_DOSAGE'
    P_IN_NUTRIENT_PTS = 'IN_NUTRIENT_PTS'
    P_NUTRIENT_FIELD = 'NUTRIENT_FIELD'
    P_THRESHOLD = 'THRESHOLD'
    P_OUT_BLOCK = 'OUT_BLOCK'

    OPTS_MODE = ["Static Dose (Standard)", "Variable Rate Analysis (VRA Precision)"]

    def name(self):
        return 'fertilizercalculator'

    def displayName(self):
        return '11. Fertilizer Calculator'

    def groupId(self):
        return 'agronomy'

    def group(self):
        return "03. Agronomy & Planting"

    def get_minimum_tier(self):
        return 'basic'

    def createInstance(self):
        return FertilizerCalculator()

    def shortHelpString(self):
        return "Menghitung kebutuhan pupuk per blok. Mendukung metode dosis statis maupun Variable Rate Analysis (VRA). Menghasilkan layer baru untuk keperluan simulasi & pengarsipan."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_IN_BLOCK,
            'Input Block (Poligon)',
            types=[QgsProcessing.TypeVectorPolygon]
        ))
        
        self.addParameter(QgsProcessingParameterField(
            self.P_TREE_COUNT_FIELD,
            'Tree Count Field (Jumlah Pokok)',
            parentLayerParameterName=self.P_IN_BLOCK,
            type=QgsProcessingParameterField.Numeric
        ))
        
        self.addParameter(QgsProcessingParameterEnum(
            self.P_MODE,
            'Calculation Mode',
            options=self.OPTS_MODE,
            defaultValue=0
        ))
        
        self.addParameter(QgsProcessingParameterString(
            self.P_FERT_TYPE,
            'Fertilizer Name / Type',
            defaultValue='NPK 13-6-27'
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_DOSAGE,
            'Standard / High Dosage per Tree (kg)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=2.5
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_FREQ,
            'Frequency per Year',
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=2
        ))
        
        # VRA Parameters
        self.addParameter(QgsProcessingParameterNumber(
            self.P_LOW_DOSAGE,
            '[VRA] Low Dosage per Tree (kg)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=1.5,
            optional=True
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_IN_NUTRIENT_PTS,
            '[VRA] Leaf Sampling Points',
            types=[QgsProcessing.TypeVectorPoint],
            optional=True
        ))
        
        self.addParameter(QgsProcessingParameterField(
            self.P_NUTRIENT_FIELD,
            '[VRA] Nutrient Value Field',
            parentLayerParameterName=self.P_IN_NUTRIENT_PTS,
            type=QgsProcessingParameterField.Numeric,
            optional=True
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_THRESHOLD,
            '[VRA] Critical Threshold (Below = High Dose)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=2.5,
            optional=True
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUT_BLOCK,
            'Simulasi Kebutuhan Pupuk (Layer Baru)',
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