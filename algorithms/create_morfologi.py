# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsFeatureSink,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext
)
from qgis.PyQt.QtCore import QVariant
from qgis import processing
from .base_algorithm import BasePlantationAlgorithm


# Morphology classification data (same as legacy ArcGIS Pro version)
MORFO_CLASSES = {
    1: {"bent_alam": "Dataran",              "kesesuaian": "Permukiman, Pertanian",      "risiko": "Rendah"},
    2: {"bent_alam": "Landai",               "kesesuaian": "Permukiman, Perkebunan",     "risiko": "Rendah"},
    3: {"bent_alam": "Perbukitan Sedang",    "kesesuaian": "Perkebunan, HTI",            "risiko": "Sedang"},
    4: {"bent_alam": "Pegunungan Terjal",    "kesesuaian": "Hutan Lindung",              "risiko": "Tinggi"},
    5: {"bent_alam": "Pegunungan Sangat Terjal", "kesesuaian": "Kawasan Lindung",        "risiko": "Sangat Tinggi"},
}

# Slope thresholds shared with CreateLereng (% rise)
# Class 1: 0-8%, 2: 8-15%, 3: 15-25%, 4: 25-45%, 5: >45%
RECLASS_TABLE = [
    0,   8,  1,
    8,  15,  2,
   15,  25,  3,
   25,  45,  4,
   45, 9999, 5,
]


class CreateMorfologi(BasePlantationAlgorithm):
    """
    QGIS Implementation of Morphology Classification tool.
    Ported from ArcGIS Pro PlantationTools.

    Pipeline:
    1.  Reproject DEM to projected CRS if input is geographic (GCS)
    2.  Compute slope raster in PERCENT_RISE via GDAL
    3.  Reclassify slope into 5 morphology classes
    4.  Polygonise the classified raster
    5.  Eliminate sliver polygons smaller than MMU (iterative)
    6.  Dissolve by class code
    7.  Attach descriptive attributes (BENT_ALAM, KESESUAIAN, RISIKO)
    """

    P_INPUT_DEM = 'INPUT_DEM'
    P_MMU_HA    = 'MMU_HA'
    P_MAX_ITER  = 'MAX_ITER'
    P_OUTPUT    = 'OUTPUT'

    def get_minimum_tier(self):
        return "free"

    def name(self):
        return 'createmorfologi'

    def displayName(self):
        return '04. Morphology Classification (Klasifikasi Morfologi)'

    def group(self):
        return '02. Topography & Hydrology'

    def groupId(self):
        return 'topography'

    def shortHelpString(self):
        return (
            "<b>Klasifikasi Morfologi Lahan</b><br>"
            "Membuat peta morfologi lahan dari raster DEM berdasarkan kemiringan lereng, "
            "menggunakan 5 kelas bentuk alam:<br>"
            "<ul>"
            "<li><b>Kelas 1 (0–8%)</b> — Dataran — Kesesuaian: Permukiman, Pertanian</li>"
            "<li><b>Kelas 2 (8–15%)</b> — Landai — Kesesuaian: Permukiman, Perkebunan</li>"
            "<li><b>Kelas 3 (15–25%)</b> — Perbukitan Sedang — Kesesuaian: Perkebunan, HTI</li>"
            "<li><b>Kelas 4 (25–45%)</b> — Pegunungan Terjal — Kesesuaian: Hutan Lindung</li>"
            "<li><b>Kelas 5 (&gt;45%)</b> — Pegunungan Sangat Terjal — Kesesuaian: Kawasan Lindung</li>"
            "</ul>"
            "<b>Minimum Mapping Unit (MMU)</b> digunakan untuk menghapus sliver polygon "
            "secara iteratif sebelum proses dissolve."
        )

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.P_INPUT_DEM,
                'Input DEM Raster'
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_MMU_HA,
                'Minimum Mapping Unit – MMU (Hektar)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1.0,
                minValue=0.01
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_MAX_ITER,
                'Maksimum Iterasi Eliminasi Sliver',
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=5,
                minValue=1,
                maxValue=20
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.P_OUTPUT,
                'Output Morfologi Lahan (Polygon)'
            )
        )

    def createInstance(self):
        return CreateMorfologi()

    # ------------------------------------------------------------------ #
    #  HELPER: auto UTM zone from raster extent                           #
    # ------------------------------------------------------------------ #
    def _get_utm_epsg(self, raster_layer):
        ext = raster_layer.extent()
        cx = (ext.xMinimum() + ext.xMaximum()) / 2
        cy = (ext.yMinimum() + ext.yMaximum()) / 2

        src_crs = raster_layer.crs()
        if not src_crs.isGeographic():
            from qgis.core import QgsCoordinateTransform
            geo_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            xform = QgsCoordinateTransform(src_crs, geo_crs, QgsCoordinateTransformContext())
            pt = xform.transform(cx, cy)
            cx, cy = pt.x(), pt.y()

        utm_zone = int((cx + 180) / 6) % 60 + 1
        epsg = 32600 + utm_zone if cy >= 0 else 32700 + utm_zone
        return epsg

    # ------------------------------------------------------------------ #
    #  MAIN                                                               #
    # ------------------------------------------------------------------ #

    def checkParameterValues(self, parameters, context):
        return super(CreateMorfologi, self).checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):
        # ---- 1. License Check ----------------------------------------- #
        self.check_license_gate()

        # ---- 2. Read Parameters --------------------------------------- #
        dem_layer = self.parameterAsRasterLayer(parameters, self.P_INPUT_DEM, context)
        mmu_ha    = self.parameterAsDouble(parameters, self.P_MMU_HA, context)
        max_iter  = self.parameterAsInt(parameters, self.P_MAX_ITER, context)

        if dem_layer is None:
            raise QgsProcessingException("Input DEM tidak valid.")

        total_steps = 7
        step = 0

        def progress(msg):
            nonlocal step
            step += 1
            feedback.setProgress(int(step / total_steps * 100))
            feedback.pushInfo(msg)

        # ---- 3. Reproject DEM if geographic --------------------------- #
        progress("1. Memeriksa sistem koordinat DEM...")
        src_crs = dem_layer.crs()
        work_dem = dem_layer

        if src_crs.isGeographic():
            epsg = self._get_utm_epsg(dem_layer)
            feedback.pushInfo(f"   DEM dalam GCS, memproyeksikan ke EPSG:{epsg}...")
            proj_res = processing.run("gdal:warpreproject", {
                'INPUT':           dem_layer,
                'SOURCE_CRS':      src_crs,
                'TARGET_CRS':      QgsCoordinateReferenceSystem(f"EPSG:{epsg}"),
                'RESAMPLING':      1,   # Bilinear
                'NODATA':          None,
                'TARGET_RESOLUTION': None,
                'OPTIONS':         '',
                'DATA_TYPE':       0,
                'TARGET_EXTENT':   None,
                'TARGET_EXTENT_CRS': None,
                'MULTITHREADING':  False,
                'EXTRA':           '',
                'OUTPUT':          'TEMPORARY_OUTPUT'
            }, context=context, feedback=feedback, is_child_algorithm=True)
            from qgis.core import QgsRasterLayer
            work_dem = QgsRasterLayer(proj_res['OUTPUT'], "dem_projected")
        else:
            feedback.pushInfo(f"   DEM sudah terproyeksi: {src_crs.authid()}")

        # ---- 4. Calculate Slope --------------------------------------- #
        progress("2. Menghitung kemiringan lereng (GDAL Slope, %)...")
        slope_res = processing.run("gdal:slope", {
            'INPUT':         work_dem,
            'BAND':          1,
            'SCALE':         1,
            'AS_PERCENT':    True,
            'COMPUTE_EDGES': True,
            'ZEVENBERGEN':   False,
            'OPTIONS':       '',
            'EXTRA':         '',
            'OUTPUT':        'TEMPORARY_OUTPUT'
        }, context=context, feedback=feedback, is_child_algorithm=True)
        slope_path = slope_res['OUTPUT']

        # ---- 5. Reclassify slope to 5 morphology classes -------------- #
        progress("3. Mengklasifikasikan kemiringan ke 5 kelas Morfologi...")
        reclass_res = processing.run("native:reclassifybytable", {
            'INPUT_RASTER':     slope_path,
            'RASTER_BAND':      1,
            'TABLE':            RECLASS_TABLE,
            'NO_DATA':          0,
            'RANGE_BOUNDARIES': 0,   # min <= val < max
            'NODATA_FOR_MISSING': True,
            'DATA_TYPE':        1,   # Int16
            'OUTPUT':           'TEMPORARY_OUTPUT'
        }, context=context, feedback=feedback, is_child_algorithm=True)
        morfo_raster_path = reclass_res['OUTPUT']

        # ---- 6. Polygonise -------------------------------------------- #
        progress("4. Mengkonversi raster Morfologi ke polygon...")
        poly_res = processing.run("gdal:polygonize", {
            'INPUT':              morfo_raster_path,
            'BAND':               1,
            'FIELD':              'DN',
            'EIGHT_CONNECTEDNESS': False,
            'EXTRA':              '',
            'OUTPUT':             'TEMPORARY_OUTPUT'
        }, context=context, feedback=feedback, is_child_algorithm=True)
        poly_path = poly_res['OUTPUT']

        # Remove nodata artefacts (DN = 0)
        filter_res = processing.run("native:extractbyexpression", {
            'INPUT':      poly_path,
            'EXPRESSION': '"DN" >= 1 AND "DN" <= 5',
            'OUTPUT':     'TEMPORARY_OUTPUT'
        }, context=context, feedback=feedback, is_child_algorithm=True)
        current_path = filter_res['OUTPUT']

        # ---- 7. Iterative sliver elimination -------------------------- #
        progress("5. Mengeliminasi sliver polygon (< MMU)...")
        mmu_m2 = mmu_ha * 10000

        iteration = 1
        while iteration <= max_iter:
            count_res = processing.run("native:extractbyexpression", {
                'INPUT':      current_path,
                'EXPRESSION': f'$area < {mmu_m2}',
                'OUTPUT':     'TEMPORARY_OUTPUT'
            }, context=context, feedback=feedback, is_child_algorithm=True)

            from qgis.core import QgsVectorLayer
            small_layer = context.getMapLayer(count_res['OUTPUT'])
            small_count = 0
            if small_layer:
                small_count = small_layer.featureCount()
            else:
                tmp = QgsVectorLayer(count_res['OUTPUT'], "tmp", "ogr")
                small_count = tmp.featureCount() if tmp.isValid() else 0

            if small_count == 0:
                feedback.pushInfo(f"   Iterasi {iteration}: Tidak ada sliver polygon tersisa.")
                break

            feedback.pushInfo(f"   Iterasi {iteration}: {small_count} polygon < {mmu_ha} Ha dieliminasi...")

            from qgis.core import QgsProcessingUtils
            layer_to_elim = QgsProcessingUtils.mapLayerFromString(current_path, context)
            if layer_to_elim:
                layer_to_elim.selectByExpression(f'$area < {mmu_m2}')

            elim_res = processing.run("qgis:eliminateselectedpolygons", {
                'INPUT':  layer_to_elim,
                'MODE':   1,   # Largest area neighbor
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }, context=context, feedback=feedback, is_child_algorithm=True)

            current_path = elim_res['OUTPUT']
            iteration += 1

        if iteration > max_iter:
            feedback.pushWarning(f"Mencapai batas maksimum iterasi ({max_iter}). Mungkin masih ada sliver kecil.")


        # ---- 8. Dissolve by morphology class -------------------------- #
        progress("6. Menggabungkan polygon per kelas Morfologi (Dissolve)...")
        dissolve_res = processing.run("native:dissolve", {
            'INPUT':  current_path,
            'FIELD':  ['DN'],
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }, context=context, feedback=feedback, is_child_algorithm=True)
        dissolved_path = dissolve_res['OUTPUT']

        # ---- 9. Build output with descriptive attributes --------------- #
        progress("7. Menambahkan atribut deskriptif dan menyimpan output...")

        out_fields = QgsFields()
        out_fields.append(QgsField('KELAS_SKL',  QVariant.Int,    len=2))
        out_fields.append(QgsField('BENT_ALAM',  QVariant.String, len=30))
        out_fields.append(QgsField('KESESUAIAN', QVariant.String, len=50))
        out_fields.append(QgsField('RISIKO',     QVariant.String, len=20))
        out_fields.append(QgsField('LUAS_HA',    QVariant.Double, prec=4))

        from qgis.core import QgsProcessingUtils
        dissolved_layer = QgsProcessingUtils.mapLayerFromString(dissolved_path, context)
        if dissolved_layer is None or not dissolved_layer.isValid():
            raise QgsProcessingException("Gagal memuat layer hasil dissolve.")

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.P_OUTPUT, context,
            out_fields,
            QgsWkbTypes.MultiPolygon,
            dissolved_layer.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException("Gagal menyiapkan output layer.")

        for feat in dissolved_layer.getFeatures():
            dn = feat['DN']
            if dn is None:
                continue
            cls = int(dn)
            info = MORFO_CLASSES.get(cls, {})

            geom = feat.geometry()
            area_ha = geom.area() / 10000.0

            new_feat = QgsFeature(out_fields)
            new_feat.setGeometry(geom)
            new_feat['KELAS_SKL']  = cls
            new_feat['BENT_ALAM']  = info.get('bent_alam',  str(cls))
            new_feat['KESESUAIAN'] = info.get('kesesuaian', '')
            new_feat['RISIKO']     = info.get('risiko',     '')
            new_feat['LUAS_HA']    = round(area_ha, 4)
            sink.addFeature(new_feat, QgsFeatureSink.FastInsert)

        feedback.pushInfo("✓ Klasifikasi Morfologi Lahan berhasil diselesaikan!")
        return {self.P_OUTPUT: dest_id}
