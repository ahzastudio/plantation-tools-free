# -*- coding: utf-8 -*-

from qgis.core import QgsProcessingException
from .base_algorithm import BasePlantationAlgorithm

_MSG = ('Fitur ini berhasil divalidasi lisensinya, namun masih dalam tahap '
        'pengembangan (porting) untuk QGIS. Silakan gunakan versi ArcGIS Pro '
        'sementara pembaruan QGIS berikutnya dirilis.')

# ---------------------------------------------------------------------------
# 00. System & Licensing
# ---------------------------------------------------------------------------
class CheckLicenseStatus(BasePlantationAlgorithm):
    def name(self): return 'checklicensestatus'
    def displayName(self): return '00a. Check License Status (Cek Status Lisensi)'
    def groupId(self): return 'system'
    def group(self): return '00. System & Licensing'
    def get_minimum_tier(self): return 'free'
    def createInstance(self): return CheckLicenseStatus()
    def initAlgorithm(self, config=None): pass
    def processAlgorithm(self, parameters, context, feedback):
        import qgis.utils
        from ..license_guard import LicenseDashboardDialog
        dialog = LicenseDashboardDialog(qgis.utils.iface.mainWindow())
        dialog.exec()
        return {}

# ---------------------------------------------------------------------------
# 01. Land Preparation
# ---------------------------------------------------------------------------
class TraverseToPolygon(BasePlantationAlgorithm):
    def name(self): return 'traversetopolygon'
    def displayName(self): return '01b. Traverse To Polygon (Survey)'
    def groupId(self): return 'land_prep'
    def group(self): return '01. Land Preparation'
    def get_minimum_tier(self): return 'free'
    def createInstance(self): return TraverseToPolygon()
    def initAlgorithm(self, config=None): pass
    def processAlgorithm(self, parameters, context, feedback):
        self.check_license_gate()
        raise QgsProcessingException(_MSG)

# ---------------------------------------------------------------------------
# 06. Environment & Conservation
# ---------------------------------------------------------------------------
class AnalisisAreaKonservasi(BasePlantationAlgorithm):
    def name(self): return 'analisisareakonservasi'
    def displayName(self): return '29. Analisis Area Konservasi (NKT / Sempadan)'
    def groupId(self): return 'environment_nkt'
    def group(self): return '08. Analisa Lingkungan & NKT'
    def get_minimum_tier(self): return 'pro'
    def createInstance(self): return AnalisisAreaKonservasi()
    def initAlgorithm(self, config=None): pass
    def processAlgorithm(self, parameters, context, feedback):
        self.check_license_gate()
        raise QgsProcessingException(_MSG)

