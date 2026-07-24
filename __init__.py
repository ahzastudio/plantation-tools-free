# -*- coding: utf-8 -*-

"""
This script initializes the QGIS plugin.
"""

def classFactory(iface):
    """
    Load PlantationToolsPlugin class from file plantation_tools_plugin.
    
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .plantation_tools_plugin import PlantationToolsPlugin
    return PlantationToolsPlugin(iface)
