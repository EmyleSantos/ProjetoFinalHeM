import time
import random
import copy
import os

# ==========================================
# 1. GERADOR DE DADOS (Simulando CUTGEN1)
# ==========================================
def gerar_arquivo_instancia(nome_arquivo, capacidade, num_tipos, min_tam, max_tam, max_demanda):
    """Gera um arquivo de texto com dados aleatórios para teste."""
    with open(nome_arquivo, 'w') as f:
        f.write(f"L= {capacidade}\n")
        f.write(f"m= {num_tipos}\n")
        
        for _ in range(num_tipos):
            tamanho = random.randint(min_tam, min(max_tam, capacidade))
            demanda = random.randint(1, max_demanda)
            f.write(f"{tamanho} {demanda}\n")
    
    return nome_arquivo

# ==========================================
# 2. LEITURA E ESTRUTURAS
# ==========================================
def ler_instancia(caminho_arquivo):
    itens_expandidos = []
    capacidade_barra = 0
    try:
        with open(caminho_arquivo, 'r') as f:
            linhas = f.readlines()
            capacidade_barra = int(linhas[0].split()[1])
            num_tipos = int(linhas[1].split()[1])
            for i in range(2, num_tipos + 2):
                dados = linhas[i].split()
                if len(dados) >= 2:
                    tamanho = int(float(dados[0]))
                    demanda = int(dados[1])
                    for _ in range(demanda):
                        itens_expandidos.append(tamanho)
        return capacidade_barra, itens_expandidos
    except FileNotFoundError:
        return None, None

def calcular_desperdicio(capacidade, barras):
    return sum(capacidade - sum(barra) for barra in barras)

def calcular_utilizacao(capacidade, barra):
    """Retorna a utilização percentual da barra"""
    return sum(barra) / capacidade if barra else 0

# ==========================================
# 3. ALGORITMOS BASE
# ==========================================
def resolver_bfd(capacidade, itens):
    """Best Fit Decreasing - aloca na barra com menor espaço sobrando"""
    inicio = time.time()
    itens_ordenados = sorted(itens, reverse=True)
    barras = []
    
    for item in itens_ordenados:
        melhor_barra = None
        menor_folga = float('inf')
        
        # Procura a barra com menor espaço sobrando que ainda caiba o item
        for barra in barras:
            espaco_livre = capacidade - sum(barra)
            if espaco_livre >= item and espaco_livre < menor_folga:
                menor_folga = espaco_livre
                melhor_barra = barra
        
        if melhor_barra is not None:
            melhor_barra.append(item)
        else:
            barras.append([item])
            
    tempo = time.time() - inicio
    desperdicio = calcular_desperdicio(capacidade, barras)
    return barras, desperdicio, tempo

def resolver_ffd(capacidade, itens):
    inicio = time.time()
    itens_ordenados = sorted(itens, reverse=True)
    barras = []
    
    for item in itens_ordenados:
        alocado = False
        for barra in barras:
            if sum(barra) + item <= capacidade:
                barra.append(item)
                alocado = True
                break
        if not alocado:
            barras.append([item])
            
    tempo = time.time() - inicio
    desperdicio = calcular_desperdicio(capacidade, barras)
    return barras, desperdicio, tempo

# ==========================================
# 4. BUSCA LOCAL MELHORADA
# ==========================================

def tentar_eliminar_barra(capacidade, solucao):
    """Tenta eliminar a barra com menor utilização realocando seus itens"""
    if len(solucao) <= 1:
        return None, False
    
    # Ordena por utilização (menor primeiro)
    solucao_ordenada = sorted(enumerate(solucao), key=lambda x: sum(x[1]))
    
    for idx_alvo, barra_alvo in solucao_ordenada[:len(solucao)//3]:  # Testa até 1/3 das barras
        if not barra_alvo:
            continue
            
        itens_realocacao = sorted(barra_alvo, reverse=True)  # Maiores primeiro
        nova_solucao = [copy.deepcopy(b) for i, b in enumerate(solucao) if i != idx_alvo]
        
        sucesso = True
        for item in itens_realocacao:
            # Tenta alocar em barras com melhor fit (menos espaço desperdiçado)
            melhor_barra = None
            menor_desperdicio = float('inf')
            
            for barra in nova_solucao:
                espaco_livre = capacidade - sum(barra)
                if espaco_livre >= item:
                    desperdicio_resultante = espaco_livre - item
                    if desperdicio_resultante < menor_desperdicio:
                        menor_desperdicio = desperdicio_resultante
                        melhor_barra = barra
            
            if melhor_barra is not None:
                melhor_barra.append(item)
            else:
                sucesso = False
                break
        
        if sucesso:
            return nova_solucao, True
    
    return None, False

def swap_entre_barras(capacidade, solucao):
    """Tenta trocar itens entre barras para melhorar utilização"""
    melhorias = []
    
    for i in range(len(solucao)):
        for j in range(i+1, len(solucao)):
            if not solucao[i] or not solucao[j]:
                continue
                
            for idx_i, item_i in enumerate(solucao[i]):
                for idx_j, item_j in enumerate(solucao[j]):
                    # Calcula desperdício antes
                    desp_antes = (capacidade - sum(solucao[i])) + (capacidade - sum(solucao[j]))
                    
                    # Simula troca
                    nova_soma_i = sum(solucao[i]) - item_i + item_j
                    nova_soma_j = sum(solucao[j]) - item_j + item_i
                    
                    if nova_soma_i <= capacidade and nova_soma_j <= capacidade:
                        desp_depois = (capacidade - nova_soma_i) + (capacidade - nova_soma_j)
                        ganho = desp_antes - desp_depois
                        
                        if ganho > 0:
                            melhorias.append((ganho, i, j, idx_i, idx_j))
    
    if melhorias:
        # Aplica a melhor troca
        melhorias.sort(reverse=True)
        _, i, j, idx_i, idx_j = melhorias[0]
        
        nova_solucao = copy.deepcopy(solucao)
        item_i = nova_solucao[i][idx_i]
        item_j = nova_solucao[j][idx_j]
        
        nova_solucao[i][idx_i] = item_j
        nova_solucao[j][idx_j] = item_i
        
        return nova_solucao, True
    
    return None, False

def realocar_item(capacidade, solucao):
    """Move um item de uma barra para outra que tenha melhor fit"""
    melhor_melhoria = 0
    melhor_movimento = None
    
    for i_origem in range(len(solucao)):
        if not solucao[i_origem]:
            continue
            
        for idx_item, item in enumerate(solucao[i_origem]):
            desp_origem_antes = capacidade - sum(solucao[i_origem])
            desp_origem_depois = capacidade - (sum(solucao[i_origem]) - item)
            
            for i_destino in range(len(solucao)):
                if i_origem == i_destino:
                    continue
                    
                nova_soma_destino = sum(solucao[i_destino]) + item
                if nova_soma_destino <= capacidade:
                    desp_destino_antes = capacidade - sum(solucao[i_destino])
                    desp_destino_depois = capacidade - nova_soma_destino
                    
                    # Ganho total
                    ganho = (desp_origem_antes + desp_destino_antes) - \
                            (desp_origem_depois + desp_destino_depois)
                    
                    if ganho > melhor_melhoria:
                        melhor_melhoria = ganho
                        melhor_movimento = (i_origem, idx_item, i_destino)
    
    if melhor_movimento:
        i_origem, idx_item, i_destino = melhor_movimento
        nova_solucao = copy.deepcopy(solucao)
        item = nova_solucao[i_origem].pop(idx_item)
        nova_solucao[i_destino].append(item)
        
        # Remove barras vazias
        nova_solucao = [b for b in nova_solucao if b]
        return nova_solucao, True
    
    return None, False

def consolidar_barras(capacidade, solucao):
    """Tenta mesclar barras parcialmente cheias"""
    if len(solucao) <= 1:
        return None, False
    
    # Ordena por utilização
    barras_ordenadas = sorted(enumerate(solucao), key=lambda x: sum(x[1]))
    
    for i in range(len(barras_ordenadas)):
        idx_i, barra_i = barras_ordenadas[i]
        
        for j in range(i+1, len(barras_ordenadas)):
            idx_j, barra_j = barras_ordenadas[j]
            
            if sum(barra_i) + sum(barra_j) <= capacidade:
                # Pode mesclar!
                nova_solucao = []
                barra_mesclada = barra_i + barra_j
                
                for k, barra in enumerate(solucao):
                    if k == idx_i:
                        nova_solucao.append(barra_mesclada)
                    elif k != idx_j:
                        nova_solucao.append(copy.deepcopy(barra))
                
                return nova_solucao, True
    
    return None, False

def busca_local_avancada(capacidade, solucao_inicial, max_iter=1000, tempo_limite=30, debug=False):
    """Busca local com múltiplas estratégias - versão agressiva"""
    inicio = time.time()
    melhor_solucao = copy.deepcopy(solucao_inicial)
    melhor_desperdicio = calcular_desperdicio(capacidade, melhor_solucao)
    melhor_num_barras = len(melhor_solucao)
    
    solucao_atual = copy.deepcopy(melhor_solucao)
    sem_melhoria = 0
    melhorias_totais = 0
    
    if debug:
        print(f"\n[DEBUG] Início: {melhor_num_barras} barras, desperdício {melhor_desperdicio}")
        print(f"[DEBUG] Utilização das barras: {[sum(b) for b in solucao_inicial[:10]]}...")
    
    for iteracao in range(max_iter):
        if time.time() - inicio > tempo_limite:
            break
        
        melhorou_nesta_iter = False
        desp_antes = calcular_desperdicio(capacidade, solucao_atual)
        barras_antes = len(solucao_atual)
        
        # FASE 1: CONSOLIDAÇÃO AGRESSIVA (executar TODAS as possíveis)
        mudou = True
        tentativas_consolidacao = 0
        while mudou and tentativas_consolidacao < 20:
            mudou = False
            nova_sol, sucesso = consolidar_barras(capacidade, solucao_atual)
            if sucesso and nova_sol and len(nova_sol) < len(solucao_atual):
                solucao_atual = nova_sol
                mudou = True
                melhorou_nesta_iter = True
                tentativas_consolidacao += 1
        
        # FASE 2: ELIMINAÇÃO DE BARRAS (mais agressivo)
        mudou = True
        tentativas_eliminacao = 0
        while mudou and tentativas_eliminacao < 10:
            mudou = False
            nova_sol, sucesso = tentar_eliminar_barra(capacidade, solucao_atual)
            if sucesso and nova_sol:
                desperdicio_novo = calcular_desperdicio(capacidade, nova_sol)
                if len(nova_sol) < len(solucao_atual):
                    solucao_atual = nova_sol
                    mudou = True
                    melhorou_nesta_iter = True
                    tentativas_eliminacao += 1
        
        # FASE 3: REALOCAÇÃO (múltiplas vezes)
        for _ in range(5):
            nova_sol, sucesso = realocar_item(capacidade, solucao_atual)
            if sucesso and nova_sol:
                novo_desp = calcular_desperdicio(capacidade, nova_sol)
                if len(nova_sol) <= len(solucao_atual) and novo_desp <= calcular_desperdicio(capacidade, solucao_atual):
                    solucao_atual = nova_sol
                    melhorou_nesta_iter = True
        
        # FASE 4: SWAP (múltiplas vezes)
        for _ in range(3):
            nova_sol, sucesso = swap_entre_barras(capacidade, solucao_atual)
            if sucesso and nova_sol:
                novo_desp = calcular_desperdicio(capacidade, nova_sol)
                if novo_desp < calcular_desperdicio(capacidade, solucao_atual):
                    solucao_atual = nova_sol
                    melhorou_nesta_iter = True
        
        # Atualiza melhor solução
        desperdicio_atual = calcular_desperdicio(capacidade, solucao_atual)
        num_barras_atual = len(solucao_atual)
        
        if num_barras_atual < melhor_num_barras or \
           (num_barras_atual == melhor_num_barras and desperdicio_atual < melhor_desperdicio):
            
            if debug and (melhor_num_barras - num_barras_atual > 0 or melhor_desperdicio - desperdicio_atual > 0):
                print(f"[DEBUG] Iter {iteracao}: {melhor_num_barras}→{num_barras_atual} barras, " \
                      f"desp {melhor_desperdicio}→{desperdicio_atual}")
            
            melhor_solucao = copy.deepcopy(solucao_atual)
            melhor_desperdicio = desperdicio_atual
            melhor_num_barras = num_barras_atual
            sem_melhoria = 0
            melhorias_totais += 1
        else:
            sem_melhoria += 1
        
        # Perturbação mais agressiva
        if sem_melhoria > 30:
            # Desfaz barras e reconstrói com FFD parcial
            if len(solucao_atual) > 3:
                # Pega todos os itens
                todos_itens = []
                for barra in solucao_atual:
                    todos_itens.extend(barra)
                
                # Pega 20% dos itens aleatoriamente
                num_perturbar = max(1, len(todos_itens) // 5)
                itens_perturbar = random.sample(todos_itens, num_perturbar)
                
                # Remove esses itens das barras
                nova_solucao = []
                for barra in solucao_atual:
                    nova_barra = [item for item in barra if item not in itens_perturbar]
                    if nova_barra:
                        nova_solucao.append(nova_barra)
                
                # Reinsere os itens com FFD
                itens_perturbar.sort(reverse=True)
                for item in itens_perturbar:
                    alocado = False
                    # Tenta best-fit
                    melhor_barra = None
                    menor_folga = float('inf')
                    
                    for barra in nova_solucao:
                        folga = capacidade - sum(barra)
                        if folga >= item and folga < menor_folga:
                            menor_folga = folga
                            melhor_barra = barra
                    
                    if melhor_barra is not None:
                        melhor_barra.append(item)
                        alocado = True
                    
                    if not alocado:
                        nova_solucao.append([item])
                
                solucao_atual = nova_solucao
                sem_melhoria = 0
                
                if debug and iteracao % 100 == 0:
                    print(f"[DEBUG] Iter {iteracao}: Perturbação aplicada")
    
    tempo = time.time() - inicio
    
    if debug:
        print(f"[DEBUG] Final: {len(melhor_solucao)} barras, desperdício {melhor_desperdicio}")
        print(f"[DEBUG] Total de melhorias: {melhorias_totais}")
    
    return melhor_solucao, melhor_desperdicio, tempo

# ==========================================
# 5. FUNÇÕES DE EXECUÇÃO
# ==========================================
def imprimir_linha_tabela(nome, res_ffd, desp_ffd, tempo_ffd, res_hib, desp_hib, tempo_hib):
    print(f"{nome:<25} | {'FFD':<10} | {len(res_ffd):<6} | {desp_ffd:<12} | {tempo_ffd:.4f}")
    
    melhoria = ""
    reducao_barras = len(res_ffd) - len(res_hib)
    reducao_desp = desp_ffd - desp_hib
    
    if reducao_barras > 0:
        melhoria = f" << -{reducao_barras} barras!"
    elif reducao_desp > 0:
        melhoria = f" << -{reducao_desp} desperdício"
    
    print(f"{'':<25} | {'BL Avançada':<10} | {len(res_hib):<6} | {desp_hib:<12} | {tempo_hib:.4f} {melhoria}")
    print("-" * 85)

def rodar_automatizado():
    print("\n>>> INICIANDO BATERIA DE 10 TESTES AUTOMATIZADOS <<<\n")
    print(f"{'Instância':<25} | {'Método':<10} | {'Barras':<6} | {'Desperdício':<12} | {'Tempo(s)':<10}")
    print("-" * 85)

    configuracoes = [
        ("Teste_01", 1000, 10, 100, 500, 5),
        ("Teste_02", 1000, 20, 50, 800, 5),
        ("Teste_03", 500,  15, 20, 100, 10),
        ("Teste_04", 2000, 50, 200, 1000, 2),
        ("Teste_05", 100,  10, 10, 90, 5),
        ("Teste_06", 1000, 100, 10, 50, 5),
        ("Teste_07", 5000, 30, 500, 2000, 3),
        ("Teste_08", 250,  20, 20, 120, 8),
        ("Teste_09", 1000, 40, 100, 400, 10),
        ("Teste_10", 1500, 25, 200, 1200, 4)
    ]

    total_reduz_barras = 0
    total_reduz_desp = 0

    for nome, cap, tipos, min_t, max_t, max_d in configuracoes:
        arquivo = gerar_arquivo_instancia(f"{nome}.txt", cap, tipos, min_t, max_t, max_d)
        cap_lida, itens = ler_instancia(arquivo)
        
        res_ffd, desp_ffd, tempo_ffd = resolver_ffd(cap_lida, itens)
        res_hib, desp_hib, tempo_hib = busca_local_avancada(cap_lida, res_ffd)
        
        if len(res_hib) < len(res_ffd):
            total_reduz_barras += 1
        if desp_hib < desp_ffd:
            total_reduz_desp += 1
        
        imprimir_linha_tabela(nome, res_ffd, desp_ffd, tempo_ffd, res_hib, desp_hib, tempo_hib)
    
    print(f"\nResumo: {total_reduz_barras}/10 testes reduziram barras | {total_reduz_desp}/10 reduziram desperdício")

def rodar_arquivo_unico():
    nome_arquivo = input("\nDigite o nome do arquivo (ex: instancia.txt): ")
    cap_lida, itens = ler_instancia(nome_arquivo)
    
    if cap_lida is None:
        print("ERRO: Arquivo não encontrado.")
        return

    print(f"\nProcessando arquivo: {nome_arquivo}...")
    print(f"Capacidade: {cap_lida} | Total de Itens: {len(itens)}")
    
    # Testa ambas heurísticas construtivas
    print("\n>>> Executando FFD...")
    res_ffd, desp_ffd, tempo_ffd = resolver_ffd(cap_lida, itens)
    
    print("\n>>> Executando BFD...")
    res_bfd, desp_bfd, tempo_bfd = resolver_bfd(cap_lida, itens)
    
    # Escolhe a melhor solução inicial
    if len(res_bfd) < len(res_ffd) or (len(res_bfd) == len(res_ffd) and desp_bfd < desp_ffd):
        print(">>> BFD produziu melhor solução inicial!")
        solucao_inicial = res_bfd
        desp_inicial = desp_bfd
        nome_metodo = "BFD"
    else:
        print(">>> FFD produziu melhor solução inicial!")
        solucao_inicial = res_ffd
        desp_inicial = desp_ffd
        nome_metodo = "FFD"
    
    print(f"\n>>> Análise da solução {nome_metodo}:")
    print(f"    Barras usadas: {len(solucao_inicial)}")
    print(f"    Desperdício total: {desp_inicial}")
    print(f"    Utilização média: {(1 - desp_inicial/(len(solucao_inicial)*cap_lida))*100:.1f}%")
    
    # Mostra distribuição de utilização
    utilizacoes = sorted([sum(b)/cap_lida for b in solucao_inicial])
    print(f"    Barras com <30% utilização: {sum(1 for u in utilizacoes if u < 0.3)}")
    print(f"    Barras com 30-60% utilização: {sum(1 for u in utilizacoes if 0.3 <= u < 0.6)}")
    print(f"    Barras com 60-90% utilização: {sum(1 for u in utilizacoes if 0.6 <= u < 0.9)}")
    print(f"    Barras com >90% utilização: {sum(1 for u in utilizacoes if u >= 0.9)}")
    
    print(f"\n>>> Executando Busca Local AGRESSIVA com DEBUG...")
    res_hib, desp_hib, tempo_hib = busca_local_avancada(cap_lida, solucao_inicial, max_iter=2000, tempo_limite=180, debug=True)
    
    print("\n" + "="*85)
    print(f"{'Instância':<25} | {'Método':<10} | {'Barras':<6} | {'Desperdício':<12} | {'Tempo(s)':<10}")
    print("-" * 85)
    imprimir_linha_tabela(nome_arquivo, solucao_inicial, desp_inicial, tempo_ffd, res_hib, desp_hib, tempo_hib)

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    print("=== SISTEMA DE TESTES: CORTE DE ESTOQUE (1DCSP) - VERSÃO MELHORADA ===")
    print("1 - Rodar bateria de 10 testes automatizados")
    print("2 - Rodar teste em um arquivo específico")
    
    opcao = input("Escolha uma opção (1 ou 2): ")
    
    if opcao == '1':
        rodar_automatizado()
    elif opcao == '2':
        rodar_arquivo_unico()
    else:
        print("Opção inválida. Reinicie o programa.")