# -*- coding: utf-8 -*-

# pyrefly: ignore [missing-import]
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFileDestination,
    QgsProcessingException,
    QgsWkbTypes,
    QgsVectorLayer,
    QgsFeatureSink,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsPoint,
    QgsLineString,
    QgsProcessingMultiStepFeedback,
    QgsField,
    QgsCoordinateTransform,
    QgsProject
)
# pyrefly: ignore [missing-import]
from qgis.PyQt.QtCore import QVariant
from .base_algorithm import BasePlantationAlgorithm
import math
import uuid

class DroneMissionPlanner(BasePlantationAlgorithm):
    P_MISSION_TYPE = 'MISSION_TYPE'
    P_AOI = 'AOI'
    P_CORRIDOR_WIDTH = 'CORRIDOR_WIDTH'
    P_DEM = 'DEM'
    P_AGL = 'AGL'
    P_OVERLAP = 'OVERLAP'
    P_METHOD = 'METHOD'
    P_ANGLE = 'ANGLE'
    P_OVERSHOOT = 'OVERSHOOT'
    P_DJI_KMZ = 'DJI_WPML_KMZ'
    P_OUTPUT = 'OUTPUT'
    P_CAMERA_PRESET = 'CAMERA_PRESET'
    P_SENSOR_W = 'SENSOR_W'
    P_SENSOR_H = 'SENSOR_H'
    P_FOCAL_L = 'FOCAL_L'
    P_FRONT_OVERLAP = 'FRONT_OVERLAP'
    P_SPEED = 'SPEED'
    P_GIMBAL_PITCH = 'GIMBAL_PITCH'
    P_RC_LOST = 'RC_LOST'
    P_RC_LOST_EXEC = 'RC_LOST_EXEC'
    P_FINISH = 'FINISH'

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'dronemissionplanner'

    def displayName(self):
        return '21. Drone Mission Planner (Terrain Follow)'

    def group(self):
        return '05. Infrastructure & Logistics'

    def groupId(self):
        return 'infrastructure'

    def createInstance(self):
        return DroneMissionPlanner()

    def shortHelpString(self):
        return "Membuat jalur terbang drone 3D (Waypoints/Path) yang dinamis mengikuti kontur permukaan (DEM) untuk menjaga konsistensi resolusi GSD."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterEnum(
            self.P_MISSION_TYPE, 'Mission Type',
            options=['Grid', 'Corridor', 'Orbit', 'Waypoint (Custom)'],
            defaultValue=0
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_AOI, 'Area of Interest (Polygon / Line / Point)', types=[QgsProcessing.TypeVectorPolygon, QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPoint]
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_CORRIDOR_WIDTH, 'Corridor Width (m) [For Line Input]',
            type=QgsProcessingParameterNumber.Integer, defaultValue=100
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_ORBIT_RADIUS, 'Orbit Radius (m) [Khusus Misi Orbit]',
            type=QgsProcessingParameterNumber.Double, defaultValue=50.0
        ))
        
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.P_DEM, 'Terrain Elevation (DEM)'
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_AGL, 'Flight Altitude (AGL - Meters)',
            type=QgsProcessingParameterNumber.Integer, defaultValue=100
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_OVERLAP, 'Side Overlap (%)',
            type=QgsProcessingParameterNumber.Integer, defaultValue=75
        ))
        
        self.addParameter(QgsProcessingParameterEnum(
            self.P_METHOD, 'Direction Method',
            options=['Manual (Enter Angle)', 'Auto (Longest Edge/Parallel)', 'Auto (Shortest/Perpendicular)'],
            defaultValue=0
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_ANGLE, 'Flight Direction/Angle (Derajat)',
            type=QgsProcessingParameterNumber.Double, defaultValue=0.0
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_OVERSHOOT, 'Turn Margin / Overshoot (m)',
            type=QgsProcessingParameterNumber.Integer, defaultValue=30
        ))
        
        self.addParameter(QgsProcessingParameterFileDestination(
            self.P_DJI_KMZ, 'Output DJI WPML KMZ File (Optional)',
            fileFilter='DJI Mission (*.kmz)', defaultValue=None, optional=True
        ))
        
        # New Camera & Mission Parameters
        self.addParameter(QgsProcessingParameterEnum(
            self.P_CAMERA_PRESET, 'Camera Sensor Preset',
            options=[
                'DJI Mavic 3 Enterprise', 'DJI Zenmuse P1 (35mm)', 'DJI Phantom 4 RTK', 'DJI Mavic 3 Multispectral',
                'DJI Mavic 3', 'DJI Mavic 3 Classic', 'DJI Mavic 3 Pro', 'DJI Mavic 4 Pro',
                'DJI Air 3', 'DJI Air 3S', 'DJI Mini 4 Pro', 'DJI Mini 5 Pro', 'DJI Lito X1',
                'Potensic Atom 2', 'Potensic Atom 3', 'Custom'
            ],
            defaultValue=0
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_SENSOR_W, 'Custom Sensor Width (mm)',
            type=QgsProcessingParameterNumber.Double, defaultValue=17.3, optional=True
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_SENSOR_H, 'Custom Sensor Height (mm)',
            type=QgsProcessingParameterNumber.Double, defaultValue=13.0, optional=True
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_FOCAL_L, 'Custom Focal Length (mm)',
            type=QgsProcessingParameterNumber.Double, defaultValue=12.29, optional=True
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_FRONT_OVERLAP, 'Front Overlap (%)',
            type=QgsProcessingParameterNumber.Integer, defaultValue=80
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_SPEED, 'Flight Speed (m/s)',
            type=QgsProcessingParameterNumber.Double, defaultValue=8.0
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_GIMBAL_PITCH, 'Gimbal Pitch Angle (Degree)',
            type=QgsProcessingParameterNumber.Integer, defaultValue=-90
        ))
        
        self.addParameter(QgsProcessingParameterEnum(
            self.P_RC_LOST, 'RC Lost Action',
            options=['goContinue', 'executeLostAction'],
            defaultValue=0
        ))
        
        self.addParameter(QgsProcessingParameterEnum(
            self.P_RC_LOST_EXEC, 'RC Lost Exec Action',
            options=['hover', 'goHome', 'land'],
            defaultValue=0
        ))
        
        self.addParameter(QgsProcessingParameterEnum(
            self.P_FINISH, 'Finish Action',
            options=['goHome', 'noAction', 'autoLand', 'goBackToStart'],
            defaultValue=0
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUTPUT, 'Output Flight Path (3D Polyline)', type=QgsProcessing.TypeVectorLine
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
def save_dji_wpml_kmz(out_kmz_path, wgs_pts, agl, side_overlap, front_overlap, speed, gimbal_pitch, rc_lost_action, rc_lost_exec, finish_action, photo_dist):
    import zipfile
    import time
    
    if not wgs_pts:
        return
        
    takeoff_lon, takeoff_lat, takeoff_alt = wgs_pts[0]
    create_time = int(time.time() * 1000)
    
    # 1. Create template.kml
    template_kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.2">
  <Document>
    <wpml:createTime>{create_time}</wpml:createTime>
    <wpml:updateTime>{create_time}</wpml:updateTime>
    <wpml:missionConfig>
      <wpml:flyToWaylineMode>safely</wpml:flyToWaylineMode>
      <wpml:finishAction>{finish_action}</wpml:finishAction>
      <wpml:exitOnRCLost>{rc_lost_action}</wpml:exitOnRCLost>
      <wpml:executeRCLostAction>{rc_lost_exec}</wpml:executeRCLostAction>
      <wpml:takeOffSecurityHeight>20</wpml:takeOffSecurityHeight>
      <wpml:takeOffRefPoint>{takeoff_lat:.7f},{takeoff_lon:.7f},{takeoff_alt:.2f}</wpml:takeOffRefPoint>
      <wpml:takeOffRefPointAGLHeight>{agl}</wpml:takeOffRefPointAGLHeight>
      <wpml:globalTransitionalSpeed>{speed}</wpml:globalTransitionalSpeed>
      <wpml:droneInfo>
        <wpml:droneEnumValue>67</wpml:droneEnumValue>
        <wpml:droneSubEnumValue>0</wpml:droneSubEnumValue>
      </wpml:droneInfo>
      <wpml:payloadInfo>
        <wpml:payloadEnumValue>52</wpml:payloadEnumValue>
        <wpml:payloadPositionIndex>0</wpml:payloadPositionIndex>
      </wpml:payloadInfo>
    </wpml:missionConfig>
    <Folder>
      <wpml:templateType>waypoint</wpml:templateType>
      <wpml:templateId>0</wpml:templateId>
      <wpml:waylineCoordinateSysParam>
        <wpml:coordinateMode>WGS84</wpml:coordinateMode>
        <wpml:heightMode>EGM96</wpml:heightMode>
      </wpml:waylineCoordinateSysParam>
      <wpml:gimbalPitchMode>usePointSetting</wpml:gimbalPitchMode>
      <wpml:globalWaypointHeadingParam>
        <wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode>
      </wpml:globalWaypointHeadingParam>
      <wpml:globalWaypointTurnMode>toPointAndStopWithDiscontinuityHeight</wpml:globalWaypointTurnMode>
      <wpml:autoFlightSpeed>{speed}</wpml:autoFlightSpeed>
    </Folder>
  </Document>
</kml>
"""

    # 2. Create waylines.wpml
    placemarks = []
    for idx, (lon, lat, alt) in enumerate(wgs_pts):
        pm = f"""      <Placemark>
        <Point>
          <coordinates>{lon:.7f},{lat:.7f},{alt:.2f}</coordinates>
        </Point>
        <wpml:index>{idx}</wpml:index>
        <wpml:executeHeight>{alt:.2f}</wpml:executeHeight>
        <wpml:waypointSpeed>{speed}</wpml:waypointSpeed>
        <wpml:waypointHeadingParam>
          <wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode>
        </wpml:waypointHeadingParam>
        <wpml:useSegmentSpeed>0</wpml:useSegmentSpeed>
        <wpml:useGlobalHeight>0</wpml:useGlobalHeight>
        <wpml:useGlobalSpeed>1</wpml:useGlobalSpeed>
        <wpml:useGlobalHeadingParam>1</wpml:useGlobalHeadingParam>
        <wpml:useGlobalTurnParam>1</wpml:useGlobalTurnParam>
      </Placemark>"""
        placemarks.append(pm)
        
    placemarks_str = "\n".join(placemarks)
    
    end_idx = max(0, len(wgs_pts) - 2)
    action_groups = f"""      <wpml:actionGroup>
        <wpml:actionGroupId>0</wpml:actionGroupId>
        <wpml:actionGroupStartIndex>0</wpml:actionGroupStartIndex>
        <wpml:actionGroupEndIndex>0</wpml:actionGroupEndIndex>
        <wpml:actionGroupMode>sequence</wpml:actionGroupMode>
        <wpml:actionTrigger>
          <wpml:actionTriggerType>reachPoint</wpml:actionTriggerType>
        </wpml:actionTrigger>
        <wpml:action>
          <wpml:actionId>0</wpml:actionId>
          <wpml:actionActuatorFunc>gimbalPitch</wpml:actionActuatorFunc>
          <wpml:actionActuatorParam>
            <wpml:gimbalPitchRotateAngle>{gimbal_pitch}</wpml:gimbalPitchRotateAngle>
            <wpml:gimbalPitchRotateMode>absoluteAngle</wpml:gimbalPitchRotateMode>
          </wpml:actionActuatorParam>
        </wpml:action>
      </wpml:actionGroup>
      <wpml:actionGroup>
        <wpml:actionGroupId>1</wpml:actionGroupId>
        <wpml:actionGroupStartIndex>0</wpml:actionGroupStartIndex>
        <wpml:actionGroupEndIndex>{end_idx}</wpml:actionGroupEndIndex>
        <wpml:actionGroupMode>sequence</wpml:actionGroupMode>
        <wpml:actionTrigger>
          <wpml:actionTriggerType>multipleDistance</wpml:actionTriggerType>
          <wpml:actionTriggerParam>
            <wpml:actionTriggerDistanceItem>{photo_dist:.2f}</wpml:actionTriggerDistanceItem>
          </wpml:actionTriggerParam>
        </wpml:actionTrigger>
        <wpml:action>
          <wpml:actionId>0</wpml:actionId>
          <wpml:actionActuatorFunc>takePhoto</wpml:actionActuatorFunc>
        </wpml:action>
      </wpml:actionGroup>"""
    
    waylines_wpml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.2">
  <Document>
    <wpml:createTime>{create_time}</wpml:createTime>
    <wpml:updateTime>{create_time}</wpml:updateTime>
    <wpml:missionConfig>
      <wpml:flyToWaylineMode>safely</wpml:flyToWaylineMode>
      <wpml:finishAction>{finish_action}</wpml:finishAction>
      <wpml:exitOnRCLost>{rc_lost_action}</wpml:exitOnRCLost>
      <wpml:executeRCLostAction>{rc_lost_exec}</wpml:executeRCLostAction>
      <wpml:takeOffSecurityHeight>20</wpml:takeOffSecurityHeight>
      <wpml:globalTransitionalSpeed>{speed}</wpml:globalTransitionalSpeed>
      <wpml:droneInfo>
        <wpml:droneEnumValue>67</wpml:droneEnumValue>
        <wpml:droneSubEnumValue>0</wpml:droneSubEnumValue>
      </wpml:droneInfo>
      <wpml:payloadInfo>
        <wpml:payloadEnumValue>52</wpml:payloadEnumValue>
        <wpml:payloadPositionIndex>0</wpml:payloadPositionIndex>
      </wpml:payloadInfo>
    </wpml:missionConfig>
    <Folder>
      <wpml:templateId>0</wpml:templateId>
      <wpml:waylineId>0</wpml:waylineId>
      <wpml:autoFlightSpeed>{speed}</wpml:autoFlightSpeed>
      <wpml:executeHeightMode>WGS84</wpml:executeHeightMode>
{placemarks_str}
{action_groups}
    </Folder>
  </Document>
</kml>
"""

    with zipfile.ZipFile(out_kmz_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('wpmz/template.kml', template_kml)
        zip_file.writestr('wpmz/waylines.wpml', waylines_wpml)
        
        # 3. Create standard doc.kml for Google Earth visualization
        coords_str = " ".join([f"{lon:.7f},{lat:.7f},{alt:.2f}" for lon, lat, alt in wgs_pts])
        doc_kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Flight Path Visualization</name>
    <Style id="yellowLine">
      <LineStyle>
        <color>7f00ffff</color>
        <width>4</width>
      </LineStyle>
    </Style>
    <Placemark>
      <name>Drone Flight Path</name>
      <styleUrl>#yellowLine</styleUrl>
      <LineString>
        <extrude>0</extrude>
        <tessellate>1</tessellate>
        <altitudeMode>absolute</altitudeMode>
        <coordinates>{coords_str}</coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>
"""
        zip_file.writestr('doc.kml', doc_kml)
