import time
import random
import copy
import os

# ==========================================
# 1. GERADOR DE DADOS (Simulando CUTGEN1)
# ==========================================
def gerar_arquivo_instancia(nome_arquivo, capacidade, num_tipos, min_tam, max_tam, max_demanda):
    """
    Gera um arquivo de texto com dados aleatórios para teste.
    """
    with open(nome_arquivo, 'w') as f:
        f.write(f"L= {capacidade}\n")
        f.write(f"m= {num_tipos}\n")
        
        for _ in range(num_tipos):
            # Gera tamanho entre min e max (garantindo que cabe na barra)
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
            # Lê exatamente m linhas
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
    desperdicio_total = 0
    for barra in barras:
        desperdicio_total += (capacidade - sum(barra))
    return desperdicio_total

# ==========================================
# 3. ALGORITMOS
# ==========================================
def resolver_ffd(capacidade, itens):
    inicio = time.time()
    # Ordena decrescente
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

def busca_local(capacidade, solucao_inicial, max_iter=1000):
    inicio = time.time()
    melhor_solucao = copy.deepcopy(solucao_inicial)
    melhor_desperdicio = calcular_desperdicio(capacidade, melhor_solucao)
    
    solucao_atual = copy.deepcopy(melhor_solucao)
    
    # Tenta melhorar por X iterações
    for _ in range(max_iter):
        # Ordena barras: as mais vazias (menor soma) primeiro para tentar eliminá-las
        solucao_atual.sort(key=lambda b: sum(b))
        
        if len(solucao_atual) <= 1:
            break

        # TENTATIVA 1: ELIMINAR BARRA
        barra_alvo = solucao_atual[0]
        itens_da_barra = list(barra_alvo)
        outras_barras = copy.deepcopy(solucao_atual[1:])
        
        sucesso_realocacao = True
        
        # Tenta encaixar itens da barra alvo nas outras
        for item in itens_da_barra:
            encaixou = False
            outras_barras.sort(key=lambda b: sum(b), reverse=True) # Tenta nas mais cheias
            
            for destino in outras_barras:
                if sum(destino) + item <= capacidade:
                    destino.append(item)
                    encaixou = True
                    break
            
            if not encaixou:
                sucesso_realocacao = False
                break
        
        if sucesso_realocacao:
            solucao_atual = outras_barras
            novo_desperdicio = calcular_desperdicio(capacidade, solucao_atual)
            if novo_desperdicio < melhor_desperdicio:
                melhor_solucao = copy.deepcopy(solucao_atual)
                melhor_desperdicio = novo_desperdicio
        else:
            # TENTATIVA 2: TROCA ALEATÓRIA (SWAP) PARA SAIR DO ÓTIMO LOCAL
            b1_idx = random.randint(0, len(solucao_atual)-1)
            b2_idx = random.randint(0, len(solucao_atual)-1)
            
            if b1_idx != b2_idx and solucao_atual[b1_idx] and solucao_atual[b2_idx]:
                item1 = solucao_atual[b1_idx].pop()
                item2 = solucao_atual[b2_idx].pop()
                
                if (sum(solucao_atual[b1_idx]) + item2 <= capacidade) and \
                   (sum(solucao_atual[b2_idx]) + item1 <= capacidade):
                    solucao_atual[b1_idx].append(item2)
                    solucao_atual[b2_idx].append(item1)
                    
                    # Se essa troca diminuiu o desperdício total
                    w_atual = calcular_desperdicio(capacidade, solucao_atual)
                    if w_atual < melhor_desperdicio:
                         melhor_solucao = copy.deepcopy(solucao_atual)
                         melhor_desperdicio = w_atual
                else:
                    # Reverte
                    solucao_atual[b1_idx].append(item1)
                    solucao_atual[b2_idx].append(item2)

    tempo = time.time() - inicio
    return melhor_solucao, melhor_desperdicio, tempo


# ==========================================
# 4. FUNÇÕES DE EXECUÇÃO
# ==========================================
def imprimir_linha_tabela(nome, res_ffd, desp_ffd, tempo_ffd, res_hib, desp_hib, tempo_hib):
    print(f"{nome:<25} | {'FFD':<10} | {len(res_ffd):<6} | {desp_ffd:<12} | {tempo_ffd:.4f}")
    
    melhoria = ""
    if len(res_hib) < len(res_ffd):
        melhoria = " << MELHOROU!"
    elif desp_hib < desp_ffd:
        melhoria = " << MENOS DESPERDÍCIO"
        
    print(f"{'':<25} | {'Híbrido':<10} | {len(res_hib):<6} | {desp_hib:<12} | {tempo_hib:.4f} {melhoria}")
    print("-" * 70)

def rodar_automatizado():
    print("\n>>> INICIANDO BATERIA DE 10 TESTES AUTOMATIZADOS <<<\n")
    print(f"{'Instância':<25} | {'Método':<10} | {'Barras':<6} | {'Desperdício':<12} | {'Tempo(s)':<10}")
    print("-" * 70)

    # Configurações: (Nome, Capacidade, Tipos, Min_Tam, Max_Tam, Max_Demanda)
    configuracoes = [
        ("Teste_01", 1000, 10, 100, 500, 5),
        ("Teste_02", 1000, 20, 50, 800, 5),
        ("Teste_03", 500,  15, 20, 100, 10),
        ("Teste_04", 2000, 50, 200, 1000, 2),
        ("Teste_05", 100,  10, 10, 90, 5),  # Itens grandes perto da capacidade
        ("Teste_06", 1000, 100, 10, 50, 5), # Muitos itens pequenos
        ("Teste_07", 5000, 30, 500, 2000, 3),
        ("Teste_08", 250,  20, 20, 120, 8),
        ("Teste_09", 1000, 40, 100, 400, 10),
        ("Teste_10", 1500, 25, 200, 1200, 4)
    ]

    for nome, cap, tipos, min_t, max_t, max_d in configuracoes:
        arquivo = gerar_arquivo_instancia(f"{nome}.txt", cap, tipos, min_t, max_t, max_d)
        cap_lida, itens = ler_instancia(arquivo)
        
        # Executa
        res_ffd, desp_ffd, tempo_ffd = resolver_ffd(cap_lida, itens)
        res_hib, desp_hib, tempo_hib = busca_local(cap_lida, res_ffd)
        
        imprimir_linha_tabela(nome, res_ffd, desp_ffd, tempo_ffd, res_hib, desp_hib, tempo_hib)

def rodar_arquivo_unico():
    nome_arquivo = input("\nDigite o nome do arquivo (ex: instancia.txt): ")
    cap_lida, itens = ler_instancia(nome_arquivo)
    
    if cap_lida is None:
        print("ERRO: Arquivo não encontrado.")
        return

    print(f"\nProcessando arquivo: {nome_arquivo}...")
    print(f"Capacidade: {cap_lida} | Total de Itens: {len(itens)}")
    print("-" * 70)
    print(f"{'Instância':<25} | {'Método':<10} | {'Barras':<6} | {'Desperdício':<12} | {'Tempo(s)':<10}")
    print("-" * 70)

    res_ffd, desp_ffd, tempo_ffd = resolver_ffd(cap_lida, itens)
    res_hib, desp_hib, tempo_hib = busca_local(cap_lida, res_ffd)
    
    imprimir_linha_tabela(nome_arquivo, res_ffd, desp_ffd, tempo_ffd, res_hib, desp_hib, tempo_hib)

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    print("=== SISTEMA DE TESTES: CORTE DE ESTOQUE (1DCSP) ===")
    print("1 - Rodar bateria de 10 testes automatizados")
    print("2 - Rodar teste em um arquivo específico")
    
    opcao = input("Escolha uma opção (1 ou 2): ")
    
    if opcao == '1':
        rodar_automatizado()
    elif opcao == '2':
        rodar_arquivo_unico()
    else:
        print("Opção inválida. Reinicie o programa.")