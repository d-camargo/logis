# -*- coding: utf-8 -*-
"""
LogisProvider: registra os algoritmos do logis na Caixa de Ferramentas.
"""

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtCore import QCoreApplication

from .algorithms.urban_network_density import UrbanNetworkDensity
from .algorithms.urban_network_connectivity import UrbanNetworkConnectivity
from .algorithms.urban_mean_circuity import UrbanMeanCircuity
from .algorithms.urban_cargo_restriction import UrbanCargoRestriction
from .algorithms.urban_demand_density import UrbanDemandDensity
from .algorithms.urban_gravity_accessibility import UrbanGravityAccessibility
from .algorithms.urban_edge_betweenness import UrbanEdgeBetweenness
from .algorithms.urban_delivery_distance import UrbanDeliveryDistance
from .algorithms.regional_network_density import RegionalNetworkDensity
from .algorithms.regional_pavement_percentage import RegionalPavementPercentage
from .algorithms.regional_critical_links import RegionalCriticalLinks


class LogisProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(UrbanNetworkDensity())
        self.addAlgorithm(UrbanNetworkConnectivity())
        self.addAlgorithm(UrbanMeanCircuity())
        self.addAlgorithm(UrbanCargoRestriction())
        self.addAlgorithm(UrbanDemandDensity())
        self.addAlgorithm(UrbanGravityAccessibility())
        self.addAlgorithm(UrbanEdgeBetweenness())
        self.addAlgorithm(UrbanDeliveryDistance())
        self.addAlgorithm(RegionalNetworkDensity())
        self.addAlgorithm(RegionalPavementPercentage())
        self.addAlgorithm(RegionalCriticalLinks())

    def id(self):
        return 'logis'

    def name(self):
        return 'logis'

    def longName(self):
        return self.tr('logis — suporte a projetos de logística no Brasil')

    def tr(self, message):
        return QCoreApplication.translate('LogisProvider', message)
