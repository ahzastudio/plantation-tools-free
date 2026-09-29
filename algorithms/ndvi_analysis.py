# -*- coding: utf-8 -*-

import os
import processing
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterVectorDestination,
    QgsProcessingException,
    QgsRasterLayer
)
from .base_algorithm import BasePlantationAlgorithm

class NDVIAnalysis(BasePlantationAlgorithm):
    P_RED_BAND = 'RED_BAND'
    P_NIR_BAND = 'NIR_BAND'
    
    P_CREATE_SHP = 'CREATE_SHP'
    
    P_OUT_NDVI = 'OUT_NDVI'
    P_OUT_DENSITY = 'OUT_DENSITY'
    P_OUT_HEALTH = 'OUT_HEALTH'
    
    P_OUT_DENSITY_SHP = 'OUT_DENSITY_SHP'
    P_OUT_HEALTH_SHP = 'OUT_HEALTH_SHP'

    def get_minimum_tier(self):
        return "basic"

    def name(self):
        return 'ndvianalysis'

    def displayName(self):
        return '14. NDVI Analysis (Vegetation Index)'

    def group(self):
        return '03. Agronomy & Planting'

    def groupId(self):
        return 'agronomy'

    def createInstance(self):
        return NDVIAnalysis()

    def shortHelpString(self):
        return "Menghitung NDVI dan mengklasifikasikannya menjadi Kerapatan & Kesehatan Vegetasi."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.P_RED_BAND,
            'Red Band (Band Merah)'
        ))
        
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.P_NIR_BAND,
            'NIR Band (Inframerah Dekat)'
        ))
        
        self.addParameter(QgsProcessingParameterBoolean(
            self.P_CREATE_SHP,
            'Create Vector Polygon (Shapefile)',
            defaultValue=False
        ))

        self.addParameter(QgsProcessingParameterRasterDestination(
            self.P_OUT_NDVI,
            'Output Raster: NDVI'
        ))
        
        self.addParameter(QgsProcessingParameterRasterDestination(
            self.P_OUT_DENSITY,
            'Output Raster: Klasifikasi Kerapatan'
        ))
        
        self.addParameter(QgsProcessingParameterRasterDestination(
            self.P_OUT_HEALTH,
            'Output Raster: Klasifikasi Kesehatan'
        ))
        
        self.addParameter(QgsProcessingParameterVectorDestination(
            self.P_OUT_DENSITY_SHP,
            'Output Vektor: Kerapatan (Jika diaktifkan)',
            optional=True
        ))
        
        self.addParameter(QgsProcessingParameterVectorDestination(
            self.P_OUT_HEALTH_SHP,
            'Output Vektor: Kesehatan (Jika diaktifkan)',
            optional=True
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