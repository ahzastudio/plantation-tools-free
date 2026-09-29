import os
import subprocess
import sys
import numpy as np

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsFeatureSink,
    QgsFeature,
    QgsGeometry,
    QgsWkbTypes,
    QgsField,
    QgsFields
)
from PyQt5.QtCore import QVariant

# Import the base class
import sys
plugin_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)
from .base_algorithm import BasePlantationAlgorithm

def ensure_dependencies(feedback):
    missing = []
    try:
        import scipy
    except ImportError:
        missing.append("scipy")
        
    if missing:
        feedback.pushInfo(f"Memulai instalasi otomatis modul yang kurang: {', '.join(missing)}...")
        try:
            python_exe = sys.executable
            subprocess.check_call([python_exe, "-m", "pip", "install"] + missing, 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            feedback.pushInfo("Instalasi berhasil! Memuat ulang modul...")
        except Exception as e:
            raise QgsProcessingException(
                f"Gagal menginstal {missing} secara otomatis. Error: {str(e)}. "
                "Silakan buka OSGeo4W Shell dan ketik: python -m pip install scipy"
            )

class LandClearingDetection(BasePlantationAlgorithm):
    P_RASTER = 'RASTER'
    P_AOI = 'AOI'
    P_EXG_THRESH = 'EXG_THRESH'
    P_WATER_MAX = 'WATER_MAX'
    P_OPENING = 'OPENING'
    P_CLOSING = 'CLOSING'
    P_OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()

    def name(self):
        return 'landclearingdetection'

    def displayName(self):
        return '24. AI Land Clearing & Road Detection'

    def group(self):
        return '04. Plantation Intelligence (AI)'

    def groupId(self):
        return 'plantation_intelligence'

    def shortHelpString(self):
        return (
            "Mendeteksi area bukaan lahan, tanah kosong, dan jalan tanah dari orthomosaic (RGB) menggunakan "
            "indeks ExG dan morfologi."
        )

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.P_RASTER, 'Input Orthomosaic (RGB)'
        ))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_AOI, 'Area of Interest (AOI Polygon)',
            types=[QgsProcessing.TypeVectorPolygon], optional=True
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_EXG_THRESH, 'Batas Maksimal ExG (Vegetasi) [Default: 26]',
            type=QgsProcessingParameterNumber.Integer, defaultValue=26
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.P_WATER_MAX, 'Batas Kecerahan Maksimal Air (Water Filter) [Default: 150]',
            type=QgsProcessingParameterNumber.Integer, defaultValue=150
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.P_OPENING, 'Filter Noise (Opening Iterations) [Default: 6]',
            type=QgsProcessingParameterNumber.Integer, defaultValue=6
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.P_CLOSING, 'Isi Lubang (Closing Iterations) [Default: 15]',
            type=QgsProcessingParameterNumber.Integer, defaultValue=15
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUTPUT, 'Output Land Clearing (Polygon)', type=QgsProcessing.TypeVectorPolygon
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