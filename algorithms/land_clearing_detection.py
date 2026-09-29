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
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec B603
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
        self.check_license_gate()
        ensure_dependencies(feedback)
        import scipy.ndimage
        
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        aoi = self.parameterAsSource(parameters, self.P_AOI, context)
        exg_thresh = self.parameterAsInt(parameters, self.P_EXG_THRESH, context)
        water_max = self.parameterAsInt(parameters, self.P_WATER_MAX, context)
        opening_iters = self.parameterAsInt(parameters, self.P_OPENING, context)
        closing_iters = self.parameterAsInt(parameters, self.P_CLOSING, context)
        
        # Ekstrak Raster Info
        provider = raster.dataProvider()
        extent = raster.extent()
        cols = raster.width()
        rows = raster.height()
        
        feedback.pushInfo(f"Menganalisis raster {cols}x{rows} piksel...")
        
        # Jika ada AOI, kita bisa membatasi extent
        if aoi:
            geom = None
            for f in aoi.getFeatures():
                if not geom:
                    geom = QgsGeometry(f.geometry())
                else:
                    geom = geom.combine(f.geometry())
            
            if geom:
                aoi_extent = geom.boundingBox()
                # Intersect extent
                extent = extent.intersect(aoi_extent)
                # Recalculate rows/cols based on extent and pixel size
                x_res = raster.rasterUnitsPerPixelX()
                y_res = raster.rasterUnitsPerPixelY()
                cols = int(extent.width() / x_res)
                rows = int(extent.height() / y_res)
        
        if cols <= 0 or rows <= 0:
            raise QgsProcessingException("Area analisis kosong/tidak valid.")
            
        block_size = 2048
        
        # Buat mask kosong untuk menampung seluruh raster (uint8)
        if (cols * rows) > (40000 * 40000):
            feedback.pushWarning("Raster sangat besar! Operasi mungkin membutuhkan RAM > 2GB.")
            
        full_mask = np.zeros((rows, cols), dtype=np.uint8)
        
        y_res = extent.height() / rows
        x_res = extent.width() / cols
        
        total_blocks = ((cols + block_size - 1) // block_size) * ((rows + block_size - 1) // block_size)
        block_idx = 0
        
        for y in range(0, rows, block_size):
            if feedback.isCanceled(): break
            h = min(block_size, rows - y)
            for x in range(0, cols, block_size):
                w = min(block_size, cols - x)
                block_idx += 1
                feedback.setProgress(int((block_idx / total_blocks) * 40))
                
                block_ext = provider.block(1, extent, cols, rows, x, y, w, h) # Red
                block_g = provider.block(2, extent, cols, rows, x, y, w, h) # Green
                block_b = provider.block(3, extent, cols, rows, x, y, w, h) # Blue
                
                if not block_ext or not block_g or not block_b:
                    continue
                    
                # Konversi ke NumPy
                R = np.frombuffer(block_ext.data(), dtype=np.uint8).reshape((h, w)).astype(np.int16)
                G = np.frombuffer(block_g.data(), dtype=np.uint8).reshape((h, w)).astype(np.int16)
                B = np.frombuffer(block_b.data(), dtype=np.uint8).reshape((h, w)).astype(np.int16)
                
                # Hitung ExG = 2G - R - B
                exg = 2 * G - R - B
                
                # Kriteria 1: ExG rendah (Tanah Kosong / Jalan)
                cleared = (exg < exg_thresh)
                
                # Kriteria 2: Water Filter (Air biasanya biru (b>=r) dan gelap)
                brightness = np.maximum.reduce([R, G, B])
                is_water = (B >= R) & (brightness <= water_max)
                
                # Kriteria 3: Bukan NoData (asumsi R=0,G=0,B=0)
                is_nodata = (R == 0) & (G == 0) & (B == 0)
                
                # Hasil akhir blok
                final_cleared = cleared & (~is_water) & (~is_nodata)
                
                full_mask[y:y+h, x:x+w] = final_cleared.astype(np.uint8)
                
        if feedback.isCanceled(): return {}
        
        feedback.pushInfo(f"Melakukan Morfologi (Opening: {opening_iters}, Closing: {closing_iters})...")
        # Struktur cross sederhana
        struct = scipy.ndimage.generate_binary_structure(2, 1)
        
        # Opening (Erosi lalu Dilasi)
        if opening_iters > 0:
            feedback.setProgressText("Morfologi: Erosion...")
            full_mask = scipy.ndimage.binary_erosion(full_mask, structure=struct, iterations=opening_iters)
            feedback.setProgressText("Morfologi: Dilation (Opening)...")
            full_mask = scipy.ndimage.binary_dilation(full_mask, structure=struct, iterations=opening_iters)
            
        # Closing (Dilasi lalu Erosi)
        if closing_iters > 0:
            feedback.setProgressText("Morfologi: Dilation (Closing)...")
            full_mask = scipy.ndimage.binary_dilation(full_mask, structure=struct, iterations=closing_iters)
            feedback.setProgressText("Morfologi: Erosion...")
            full_mask = scipy.ndimage.binary_erosion(full_mask, structure=struct, iterations=closing_iters)
            
        feedback.setProgress(80)
        feedback.setProgressText("Konversi ke Poligon...")
        
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_tif = os.path.join(temp_dir, 'plantation_mask.tif')
        
        from osgeo import gdal, osr, ogr
        driver = gdal.GetDriverByName('GTiff')
        ds = driver.Create(temp_tif, cols, rows, 1, gdal.GDT_Byte)
        ds.SetGeoTransform((extent.xMinimum(), x_res, 0, extent.yMaximum(), 0, -y_res))
        
        srs = osr.SpatialReference()
        srs.ImportFromWkt(raster.crs().toWkt())
        ds.SetProjection(srs.ExportToWkt())
        
        band = ds.GetRasterBand(1)
        band.WriteArray(full_mask.astype(np.uint8))
        band.SetNoDataValue(0)
        
        mem_drv = ogr.GetDriverByName('Memory')
        mem_ds = mem_drv.CreateDataSource('out')
        mem_layer = mem_ds.CreateLayer('clearing', srs, ogr.wkbPolygon)
        new_field = ogr.FieldDefn('value', ogr.OFTInteger)
        mem_layer.CreateField(new_field)
        
        gdal.Polygonize(band, band, mem_layer, 0, [], callback=None)
        ds = None # Close raster
        
        fields = QgsFields()
        fields.append(QgsField("Status", QVariant.String))
        fields.append(QgsField("Area_Ha", QVariant.Double))
        
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.P_OUTPUT, context, fields,
            QgsWkbTypes.Polygon, raster.crs()
        )
        
        mem_layer.ResetReading()
        feat = mem_layer.GetNextFeature()
        count = 0
        while feat:
            geom = feat.GetGeometryRef()
            if geom:
                qgs_geom = QgsGeometry.fromWkt(geom.ExportToWkt())
                # Hanya simpan area > 10 sqm
                if qgs_geom.area() > 10.0:
                    out_feat = QgsFeature(fields)
                    out_feat.setGeometry(qgs_geom)
                    out_feat.setAttribute("Status", "Bukaan Lahan")
                    out_feat.setAttribute("Area_Ha", qgs_geom.area() / 10000.0)
                    sink.addFeature(out_feat)
                    count += 1
            feat = mem_layer.GetNextFeature()
            
        mem_ds = None
        
        try:
            os.remove(temp_tif)
        except:
            pass
            
        feedback.pushInfo(f"Selesai! {count} area bukaan lahan terdeteksi.")
        return {self.P_OUTPUT: dest_id}
