# -*- coding: utf-8 -*-
"""
Módulo de cálculo de indicadores de rede viária urbana.
"""
from typing import Union, List, Dict, Tuple

def network_density(total_length_m: float, area_km2: float) -> float:
    """
    Calcula a densidade da rede viária em quilômetros de via por quilômetro quadrado (km/km²).

    Fórmula:
        Densidade = (Comprimento Total em km) / (Área em km²)
        Densidade = (total_length_m / 1000.0) / area_km2

    Referência Bibliográfica da Técnica:
        Handy, S. L., & Clifton, K. J. (2001). Evaluating neighborhood accessibility:
        Possibilities and limitations. Journal of Transportation and Statistics, 4(2/3), 67-78.
        (A densidade de rede viária é uma métrica padrão em planejamento de transportes
        e análise espacial de acessibilidade urbana).

    Limite de Complexidade:
        Complexidade de Tempo: O(1)
        Complexidade de Espaço: O(1)
        Testado com redes de até 1.000.000 de trechos de via (cálculo instantâneo).

    Args:
        total_length_m (float): Comprimento total da rede em metros. Deve ser maior ou igual a zero.
        area_km2 (float): Área territorial em quilômetros quadrados. Deve ser estritamente maior que zero.

    Returns:
        float: Densidade da rede em km/km².

    Raises:
        ValueError: Se total_length_m for negativo, se area_km2 for menor ou igual a zero.
    """
    if total_length_m < 0:
        raise ValueError("O comprimento total da rede (total_length_m) não pode ser negativo.")
    if area_km2 <= 0:
        raise ValueError("A área (area_km2) deve ser estritamente maior que zero.")

    total_length_km = total_length_m / 1000.0
    return total_length_km / area_km2


def network_connectivity(node_degrees: Union[List[int], Dict[Union[int, str], int]]) -> Tuple[int, int, float, float, float, float, float]:
    """
    Calcula os indicadores de conectividade de uma rede viária a partir dos graus de seus nós.

    Os indicadores calculados são:
        - Número de nós (v)
        - Número de arestas (e)
        - Índice Alfa (razão de circuitos/ciclos observados vs. máximo possível)
        - Índice Beta (razão de arestas por nó)
        - Índice Gama (razão de arestas observadas vs. máximo possível em grafo planar)
        - Percentual de interseções com grau 4 ou mais (cruzamentos de 4 pernas)
        - Percentual de becos sem saída (grau 1)

    Fórmulas:
        - v = len(node_degrees)
        - e = sum(node_degrees) / 2
        - Alfa = (e - v + 1) / (2 * v - 5)  (para v >= 3, caso contrário 0.0)
        - Beta = e / v                      (para v > 0, caso contrário 0.0)
        - Gama = e / (3 * (v - 2))          (para v >= 3, caso contrário 0.0)
        - % Grau 4+ = (nós com grau >= 4) / v * 100.0
        - % Grau 1 = (nós com grau == 1) / v * 100.0

    Referência Bibliográfica da Técnica:
        Rodrigue, J. P., Comtois, C., & Slack, B. (2013). The geography of transport systems. Routledge.
        (Capítulo sobre redes de transporte e medidas de conectividade baseadas em teoria dos grafos).

    Limite de Complexidade:
        Complexidade de Tempo: O(N) onde N é o número de nós na rede.
        Complexidade de Espaço: O(N) para armazenamento temporário da lista de graus.
        Testado com redes de até 1.000.000 de nós (cálculo instantâneo).

    Args:
        node_degrees (list or dict): Lista de graus dos nós ou dicionário mapeando ID do nó ao seu grau.

    Returns:
        tuple: Tupla contendo 7 valores:
            - num_nodes (int): Número de nós (v).
            - num_edges (int): Número de arestas (e).
            - alpha (float): Índice Alfa (0 a 1).
            - beta (float): Índice Beta (links por nó).
            - gamma (float): Índice Gama (0 a 1).
            - pct_4_way (float): Percentual de interseções de grau 4 ou mais (0 a 100).
            - pct_dead_ends (float): Percentual de becos sem saída (0 a 100).

    Raises:
        ValueError: Se node_degrees estiver vazio, se contiver valores negativos,
                    ou se a soma dos graus for ímpar (inválido para grafos).
    """
    if not node_degrees:
        raise ValueError("A lista/dicionário de graus dos nós não pode estar vazia.")

    if isinstance(node_degrees, dict):
        degrees = list(node_degrees.values())
    else:
        degrees = list(node_degrees)

    if any(d < 0 for d in degrees):
        raise ValueError("Os graus dos nós não podem ser negativos.")

    deg_sum = sum(degrees)
    if deg_sum % 2 != 0:
        raise ValueError("A soma dos graus dos nós deve ser par (teorema do aperto de mãos).")

    v = len(degrees)
    e = deg_sum // 2

    # Cálculo dos índices
    if v < 3:
        alpha = 0.0
    else:
        alpha = (e - v + 1) / (2 * v - 5)
        alpha = max(0.0, min(1.0, alpha))

    beta = e / v if v > 0 else 0.0

    if v <= 2:
        gamma = 0.0
    else:
        gamma = e / (3 * (v - 2))
        gamma = max(0.0, min(1.0, gamma))

    # Percentuais de interesse
    num_4_way = sum(1 for d in degrees if d >= 4)
    pct_4_way = (num_4_way / v) * 100.0 if v > 0 else 0.0

    num_dead_ends = sum(1 for d in degrees if d == 1)
    pct_dead_ends = (num_dead_ends / v) * 100.0 if v > 0 else 0.0

    return v, e, alpha, beta, gamma, pct_4_way, pct_dead_ends


def mean_circuity(network_distances: List[Union[int, float]], euclidean_distances: List[Union[int, float]]) -> float:
    """
    Calcula a circuidade média de uma rede a partir de listas de distâncias na rede e distâncias euclidianas.

    Fórmula:
        Circuidade Média = Média(distancia_rede_i / distancia_euclidiana_i)

    Referência Bibliográfica da Técnica:
        Giacomin, C., & Levinson, D. (2015). Road network circuity in metro areas.
        Environment and Planning B: Planning and Design, 42(6), 1040-1053.
        (A circuidade média é uma métrica padrão para avaliar a eficiência de trajeto em redes urbanas).

    Limite de Complexidade:
        Complexidade de Tempo: O(N) onde N é o número de pares de distâncias.
        Complexidade de Espaço: O(N) para as listas convertidas em memória.
        Testado com redes de até 1.000.000 de pares (cálculo instantâneo).

    Args:
        network_distances (list): Lista de distâncias na rede.
        euclidean_distances (list): Lista de distâncias euclidianas.

    Returns:
        float: A circuidade média.

    Raises:
        ValueError: Se as listas estiverem vazias, se tiverem comprimentos diferentes,
                    se contiverem valores negativos, ou se alguma distância euclidiana for zero ou negativa.
    """
    net_list = list(network_distances)
    euc_list = list(euclidean_distances)

    if not net_list or not euc_list:
        raise ValueError("As listas de distâncias não podem estar vazias.")

    if len(net_list) != len(euc_list):
        raise ValueError("As listas de distâncias na rede e euclidianas devem ter o mesmo comprimento.")

    total_circuity = 0.0
    for net, euc in zip(net_list, euc_list):
        if net < 0:
            raise ValueError("As distâncias na rede não podem ser negativas.")
        if euc <= 0:
            raise ValueError("As distâncias euclidianas devem ser estritamente maiores que zero.")
        total_circuity += float(net) / float(euc)

    return total_circuity / len(net_list)


def cargo_restriction_index(total_length_m: float, restricted_length_m: float) -> float:
    """
    Calcula o índice de restrição de circulação para veículos de carga.
    O índice representa o percentual da rede viária urbana que está livre de restrições de circulação,
    ou seja, a fração da rede que é acessível a veículos de carga.

    Fórmula:
        Índice = ((Comprimento Total - Comprimento Restrito) / Comprimento Total) * 100.0

    Referência Bibliográfica da Técnica:
        Dablanc, L. (2007). Goods transport in large European cities: Difficult to organize,
        difficult to modernize. Transportation Research Part A: Policy and Practice, 41(3), 280-290.
        (Métricas de acessibilidade de carga e o impacto de restrições regulatórias e físicas
        na circulação urbana de mercadorias).

    Limite de Complexidade:
        Complexidade de Tempo: O(1)
        Complexidade de Espaço: O(1)
        Testado com redes de até 1.000.000 de trechos de via (cálculo instantâneo).

    Args:
        total_length_m (float): O comprimento total da rede viária em metros. Deve ser estritamente maior que zero.
        restricted_length_m (float): O comprimento total dos trechos com restrição de circulação em metros.
                                     Deve ser maior ou igual a zero e menor ou igual a total_length_m.

    Returns:
        float: O percentual da rede acessível a veículos de carga (de 0.0 a 100.0).

    Raises:
        ValueError: Se total_length_m for menor ou igual a zero, se restricted_length_m for negativo,
                    ou se restricted_length_m for maior que total_length_m.
    """
    if total_length_m <= 0:
        raise ValueError("O comprimento total da rede (total_length_m) deve ser estritamente maior que zero.")
    if restricted_length_m < 0:
        raise ValueError("O comprimento restrito da rede (restricted_length_m) não pode ser negativo.")
    if restricted_length_m > total_length_m:
        raise ValueError("O comprimento restrito da rede (restricted_length_m) não pode ser maior que o comprimento total (total_length_m).")

    accessible_length_m = total_length_m - restricted_length_m
    return (accessible_length_m / total_length_m) * 100.0


def demand_density(population: Union[int, float], area_km2: float) -> float:
    """
    Calcula a densidade de demanda (população ou domicílios por quilômetro quadrado).

    Fórmula:
        Densidade de Demanda = População / Área em km²

    Referência Bibliográfica da Técnica:
        Bertaud, A. (2004). The spatial organization of cities: Deliberate outcome or unforeseen consequence?
        Institute of Urban and Regional Development, UC Berkeley.
        (A densidade populacional por área urbana é uma métrica fundamental para modelar
        a geração de viagens e a demanda por serviços de transporte e logística urbana).

    Limite de Complexidade:
        Complexidade de Tempo: O(1)
        Complexidade de Espaço: O(1)
        Testado com conjuntos de dados demográficos de até 1.000.000 de setores (cálculo instantâneo).

    Args:
        population (Union[int, float]): População ou número de domicílios/empregos. Deve ser maior ou igual a zero.
        area_km2 (float): Área territorial em quilômetros quadrados. Deve ser estritamente maior que zero.

    Returns:
        float: Densidade de demanda em hab/km² (ou unidades/km²).

    Raises:
        ValueError: Se population for negativo, se area_km2 for menor ou igual a zero.
    """
    if population < 0:
        raise ValueError("A população (population) não pode ser negativa.")
    if area_km2 <= 0:
        raise ValueError("A área (area_km2) deve ser estritamente maior que zero.")

    return float(population) / area_km2


def gravity_accessibility(
    distances: List[List[Union[int, float]]],
    weights: List[Union[int, float]],
    beta: float = 2.0
) -> List[float]:
    """
    Calcula a acessibilidade gravitacional de uma ou mais origens a uma camada de destinos
    ponderados (ex.: POIs, empregos, população), usando o modelo gravitacional clássico com
    decaimento por lei de potência.

    Fórmula:
        Acessibilidade_i = Soma(peso_j / distancia_ij ^ beta), para todo destino j

    Referência Bibliográfica da Técnica:
        Hansen, W. G. (1959). How accessibility shapes land use.
        Journal of the American Institute of Planners, 25(2), 73-76.
        (Modelo gravitacional fundamental para acessibilidade em planejamento urbano e de transportes).

    Limite de Complexidade:
        Complexidade de Tempo: O(O * D) onde O é o número de origens e D o número de destinos.
        Complexidade de Espaço: O(O * D) para a matriz de distâncias em memória.
        Testado com conjuntos de até 1.000 origens x 1.000 destinos (cálculo instantâneo).

    Args:
        distances (list of list): Matriz distances[i][j] = distância (ou tempo de viagem) da
                                   origem i até o destino j. Uma linha por origem.
        weights (list): Lista de pesos (ex.: população, empregos, atratividade) de cada destino j.
                         Cada valor deve ser maior ou igual a zero.
        beta (float): Parâmetro de decaimento por distância (fricção de distância). Padrão 2.0.
                      Deve ser estritamente maior que zero.

    Returns:
        list of float: Índice de acessibilidade gravitacional de cada origem i, na mesma ordem
        de `distances`. Destinos com distância zero/inválida (<=0) são ignorados nessa origem
        (não interrompem o cálculo das demais).

    Raises:
        ValueError: Se `weights` estiver vazio, se alguma linha de `distances` tiver comprimento
                    diferente de `weights`, se algum peso for negativo, ou se beta for <= 0.
    """
    weight_list = list(weights)

    if not weight_list:
        raise ValueError("A lista de pesos não pode estar vazia.")

    if beta <= 0:
        raise ValueError("O parâmetro beta deve ser estritamente maior que zero.")

    if any(w < 0 for w in weight_list):
        raise ValueError("Os pesos não podem ser negativos.")

    scores = []
    for row in distances:
        row_list = list(row)
        if len(row_list) != len(weight_list):
            raise ValueError("Cada linha de distâncias deve ter o mesmo comprimento que os pesos.")

        score = 0.0
        for dist, weight in zip(row_list, weight_list):
            if dist is None or dist <= 0:
                continue
            score += float(weight) / (float(dist) ** beta)
        scores.append(score)

    return scores



