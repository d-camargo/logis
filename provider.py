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
from .algorithms.facility_p_median import FacilityPMedian
from .algorithms.facility_mclp import FacilityMCLP
from .algorithms.facility_lscp import FacilityLSCP
from .algorithms.vrp_cvrp import VrpCvrp
from .algorithms.waste_generation_estimate import WasteGenerationEstimate
from .algorithms.waste_districting import WasteDistricting
from .algorithms.waste_cpp_route import WasteCppRoute


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
        self.addAlgorithm(FacilityPMedian())
        self.addAlgorithm(FacilityMCLP())
        self.addAlgorithm(FacilityLSCP())
        self.addAlgorithm(VrpCvrp())
        self.addAlgorithm(WasteGenerationEstimate())
        self.addAlgorithm(WasteDistricting())
        self.addAlgorithm(WasteCppRoute())

    def id(self):
        return 'logis'

    def name(self):
        return 'logis'

    def longName(self):
        return self.tr('logis — suporte a projetos de logística no Brasil')

    def tr(self, message):
        return QCoreApplication.translate('LogisProvider', message)
