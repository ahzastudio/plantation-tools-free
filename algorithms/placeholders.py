# -*- coding: utf-8 -*-

from qgis.core import QgsProcessingException
from .base_algorithm import BasePlantationAlgorithm

_MSG = ('Fitur ini berhasil divalidasi lisensinya, namun masih dalam tahap '
        'pengembangan (porting) untuk QGIS. Silakan gunakan versi ArcGIS Pro '
        'sementara pembaruan QGIS berikutnya dirilis.')

# ---------------------------------------------------------------------------
# 02. Topography & Hydrology
# ---------------------------------------------------------------------------
class CreateLereng(BasePlantationAlgorithm):
    def name(self): return 'createlereng'
    def displayName(self): return '03. Slope Classification (Klasifikasi Lereng)'
    def groupId(self): return 'topography'
    def group(self): return '02. Topography & Hydrology'
    def get_minimum_tier(self): return 'free'
    def createInstance(self): return CreateLereng()
    def initAlgorithm(self, config=None): pass
    def processAlgorithm(self, parameters, context, feedback):
        self.check_license_gate()
        raise QgsProcessingException(_MSG)

class CreateMorfologi(BasePlantationAlgorithm):
    def name(self): return 'createmorfologi'
    def displayName(self): return '04. Morphology Classification (Klasifikasi Morfologi)'
    def groupId(self): return 'topography'
    def group(self): return '02. Topography & Hydrology'
    def get_minimum_tier(self): return 'free'
    def createInstance(self): return CreateMorfologi()
    def initAlgorithm(self, config=None): pass
    def processAlgorithm(self, parameters, context, feedback):
        self.check_license_gate()
        raise QgsProcessingException(_MSG)

# ---------------------------------------------------------------------------
# 07. Analisa Infrastruktur Jalan
# ---------------------------------------------------------------------------
class RoadDensityAnalysis(BasePlantationAlgorithm):
    def name(self): return 'roaddensityanalysis'
    def displayName(self): return '24. Analisa Kerapatan & Panjang Jalan'
    def groupId(self): return 'roads'
    def group(self): return '07. Analisa Infrastruktur (Jalan & Parit)'
    def get_minimum_tier(self): return 'basic'
    def createInstance(self): return RoadDensityAnalysis()
    def initAlgorithm(self, config=None): pass
    def processAlgorithm(self, parameters, context, feedback):
        self.check_license_gate()
        raise QgsProcessingException(_MSG)

class RoadBufferAnalysis(BasePlantationAlgorithm):
    def name(self): return 'roadbufferanalysis'
    def displayName(self): return '25. Buffer & Luas Jalan'
    def groupId(self): return 'roads'
    def group(self): return '07. Analisa Infrastruktur (Jalan & Parit)'
    def get_minimum_tier(self): return 'basic'
    def createInstance(self): return RoadBufferAnalysis()
    def initAlgorithm(self, config=None): pass
    def processAlgorithm(self, parameters, context, feedback):
        self.check_license_gate()
        raise QgsProcessingException(_MSG)

class RoadAreaLossAnalysis(BasePlantationAlgorithm):
    def name(self): return 'roadarealossanalysis'
    def displayName(self): return '26. Analisa Luas Terpotong Jalan'
    def groupId(self): return 'roads'
    def group(self): return '07. Analisa Infrastruktur (Jalan & Parit)'
    def get_minimum_tier(self): return 'basic'
    def createInstance(self): return RoadAreaLossAnalysis()
    def initAlgorithm(self, config=None): pass
    def processAlgorithm(self, parameters, context, feedback):
        self.check_license_gate()
        raise QgsProcessingException(_MSG)

# ---------------------------------------------------------------------------
# 07. Analisa Parit & Drainase
# ---------------------------------------------------------------------------
class DrainDensityAnalysis(BasePlantationAlgorithm):
    def name(self): return 'draindensityanalysis'
    def displayName(self): return '21. Analisa Kerapatan & Panjang Parit'
    def groupId(self): return 'drainage'
    def group(self): return '07. Analisa Infrastruktur (Jalan & Parit)'
    def get_minimum_tier(self): return 'basic'
    def createInstance(self): return DrainDensityAnalysis()
    def initAlgorithm(self, config=None): pass
    def processAlgorithm(self, parameters, context, feedback):
        self.check_license_gate()
        raise QgsProcessingException(_MSG)

class DrainBufferAnalysis(BasePlantationAlgorithm):
    def name(self): return 'drainbufferanalysis'
    def displayName(self): return '22. Buffer & Luas Parit'
    def groupId(self): return 'drainage'
    def group(self): return '07. Analisa Infrastruktur (Jalan & Parit)'
    def get_minimum_tier(self): return 'basic'
    def createInstance(self): return DrainBufferAnalysis()
    def initAlgorithm(self, config=None): pass
    def processAlgorithm(self, parameters, context, feedback):
        self.check_license_gate()
        raise QgsProcessingException(_MSG)

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
# 08. Analisa Lingkungan & NKT
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
