# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsFeatureSink,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsFields,
    QgsField,
    QgsWkbTypes
)
from qgis.PyQt.QtCore import QVariant
import math
import string
from .base_algorithm import BasePlantationAlgorithm

class CreateBlockGrid(BasePlantationAlgorithm):
    """
    QGIS Implementation of Create Block Grid tool.
    Ported from ArcGIS Pro PlantationTools_v1.2.3.pyt.
    """
    
    P_INPUT = 'INPUT'
    P_BLOCK_WIDTH = 'BLOCK_WIDTH'
    P_BLOCK_LENGTH = 'BLOCK_LENGTH'
    P_MAIN_ROAD_WIDTH = 'MAIN_ROAD_WIDTH'
    P_COLL_ROAD_WIDTH = 'COLL_ROAD_WIDTH'
    P_ROTATION = 'ROTATION'
    P_OUTPUT = 'OUTPUT'

    def get_minimum_tier(self):
        return "free"

    def name(self):
        return 'createblockgrid'

    def displayName(self):
        return '01. Create Block Grid (Membuat Grid Blok)'

    def group(self):
        return '01. Land Preparation'

    def groupId(self):
        return 'land_prep'

    def shortHelpString(self):
        return "Creates a grid of plantation blocks based on defined dimensions and road widths.\nPastikan CRS layer dalam satuan meter (Projected UTM)."

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.P_INPUT,
                'Boundary / Extent (Polygon Layer)',
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_BLOCK_WIDTH,
                'Block Width (Lebar Blok) dalam Meter',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1000.0
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_BLOCK_LENGTH,
                'Block Length (Panjang Blok) dalam Meter',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=300.0
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_MAIN_ROAD_WIDTH,
                'Main Road Width (Lebar Jalan Utama) dalam Meter',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=9.0
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_COLL_ROAD_WIDTH,
                'Collection Road Width (Jalan Panen) dalam Meter',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=7.0
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_ROTATION,
                'Grid Rotation Angle (Degrees)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.P_OUTPUT,
                'Output Block Grid'
            )
        )

    def createInstance(self):
        return CreateBlockGrid()


    def checkParameterValues(self, parameters, context):
        return super(CreateBlockGrid, self).checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):
        # 1. License Check
        self.check_license_gate()
        
        # 2. Extract Parameters
        source = self.parameterAsSource(parameters, self.P_INPUT, context)
        block_width = self.parameterAsDouble(parameters, self.P_BLOCK_WIDTH, context)
        block_length = self.parameterAsDouble(parameters, self.P_BLOCK_LENGTH, context)
        main_road_w = self.parameterAsDouble(parameters, self.P_MAIN_ROAD_WIDTH, context)
        coll_road_w = self.parameterAsDouble(parameters, self.P_COLL_ROAD_WIDTH, context)
        rotation = self.parameterAsDouble(parameters, self.P_ROTATION, context)

        if source is None:
            raise QgsProcessingException("Input layer tidak valid.")

        if source.sourceCrs().isGeographic():
            feedback.pushWarning("PERINGATAN: CRS Input bersifat Geographic (Derajat). Tools ini mengharuskan Projected CRS (Meter) seperti UTM agar luas dan dimensi akurat.")

        # 3. Output Setup
        fields = QgsFields()
        fields.append(QgsField('BLOCK_ID', QVariant.String, len=20))
        fields.append(QgsField('ROW_ID', QVariant.Int))
        fields.append(QgsField('COL_ID', QVariant.String, len=5))
        fields.append(QgsField('TYPE', QVariant.String, len=20))
        fields.append(QgsField('LUAS_HA', QVariant.Double))
        fields.append(QgsField('PETAK', QVariant.String, len=20))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.P_OUTPUT, context,
            fields, QgsWkbTypes.Polygon, source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException("Gagal menyiapkan output layer.")

        # 4. Extract True Geometry Extent
        features = source.getFeatures()
        geoms = []
        for feat in features:
            if feat.hasGeometry():
                geoms.append(feat.geometry())

        if not geoms:
            raise QgsProcessingException("Input layer tidak memiliki fitur geometri.")

        boundary_geom = geoms[0]
        for i in range(1, len(geoms)):
            boundary_geom = boundary_geom.combine(geoms[i])

        bbox = boundary_geom.boundingBox()
        origin_x = bbox.xMinimum()
        origin_y = bbox.yMinimum()
        center_x = bbox.center().x()
        center_y = bbox.center().y()

        diag_length = math.sqrt(bbox.width()**2 + bbox.height()**2)
        safe_dist = diag_length * 0.75
        bound_min_x = center_x - safe_dist
        bound_max_x = center_x + safe_dist
        bound_min_y = center_y - safe_dist
        bound_max_y = center_y + safe_dist

        x_step = block_width + main_road_w
        y_step = block_length + coll_road_w

        start_col = math.floor((bound_min_x - origin_x) / x_step)
        end_col   = math.ceil((bound_max_x - origin_x) / x_step)
        num_cols  = end_col - start_col
        start_x   = origin_x + (start_col * x_step)

        start_row = math.floor((bound_min_y - origin_y) / y_step)
        end_row   = math.ceil((bound_max_y - origin_y) / y_step)
        num_rows  = end_row - start_row
        start_y   = origin_y + (start_row * y_step)

        rad_rot = math.radians(-rotation)
        sin_rot = math.sin(rad_rot)
        cos_rot = math.cos(rad_rot)

        def rotate_point(px, py, cx, cy):
            tx = px - cx
            ty = py - cy
            rx = tx * cos_rot - ty * sin_rot
            ry = tx * sin_rot + ty * cos_rot
            return rx + cx, ry + cy

        total_steps = num_rows * num_cols
        step = 0
        blocks_created = 0

        # Processing loop
        for r in range(num_rows):
            if feedback.isCanceled():
                break
            
            y_base = start_y + (r * y_step)
            for c in range(num_cols):
                x_base = start_x + (c * x_step)

                # Polygons corners definition (Local coords)
                b_p1 = (x_base, y_base)
                b_p2 = (x_base + block_width, y_base)
                b_p3 = (x_base + block_width, y_base + block_length)
                b_p4 = (x_base, y_base + block_length)

                mr_p1 = (x_base + block_width, y_base)
                mr_p2 = (x_base + block_width + main_road_w, y_base)
                mr_p3 = (x_base + block_width + main_road_w, y_base + y_step)
                mr_p4 = (x_base + block_width, y_base + y_step)

                cr_p1 = (x_base, y_base + block_length)
                cr_p2 = (x_base + block_width, y_base + block_length)
                cr_p3 = (x_base + block_width, y_base + block_length + coll_road_w)
                cr_p4 = (x_base, y_base + block_length + coll_road_w)

                def process_poly(points, p_type, blk_id=""):
                    rot_pts = [rotate_point(p[0], p[1], center_x, center_y) for p in points]
                    
                    qgs_pts = [QgsPointXY(p[0], p[1]) for p in rot_pts]
                    geom = QgsGeometry.fromPolygonXY([qgs_pts])

                    if not geom.disjoint(boundary_geom):
                        # Calculate Hectares
                        area_ha = geom.area() / 10000.0
                        
                        col_char = string.ascii_uppercase[c % 26]
                        if c >= 26: col_char = "A" + col_char
                        
                        feat = QgsFeature(fields)
                        feat.setGeometry(geom)
                        feat.setAttribute('BLOCK_ID', blk_id)
                        feat.setAttribute('ROW_ID', r + 1)
                        feat.setAttribute('COL_ID', col_char)
                        feat.setAttribute('TYPE', p_type)
                        feat.setAttribute('LUAS_HA', area_ha)
                        feat.setAttribute('PETAK', blk_id)
                        
                        sink.addFeature(feat, QgsFeatureSink.FastInsert)
                        return 1
                    return 0

                col_char = string.ascii_uppercase[c % 26]
                if c >= 26: col_char = "A" + col_char
                blk_id = f"{col_char}-{r+1:03d}"

                # Insert features
                blocks_created += process_poly([b_p1, b_p2, b_p3, b_p4], "BLOCK", blk_id)
                if main_road_w > 0:
                    process_poly([mr_p1, mr_p2, mr_p3, mr_p4], "MAIN_ROAD")
                if coll_road_w > 0:
                    process_poly([cr_p1, cr_p2, cr_p3, cr_p4], "COLLECTION_ROAD")

                step += 1
                feedback.setProgress(int(step * 100 / total_steps))

        feedback.pushInfo(f"Berhasil membuat {blocks_created} blok perkebunan.")
        return {self.P_OUTPUT: dest_id}
