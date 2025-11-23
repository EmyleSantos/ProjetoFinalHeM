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
            # Pula a linha 1 (número de tipos) e lê o resto
            # for linha in linhas[2:]:
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
    """
    Iterated Local Search (ILS) para 1DCSP.
    - capacidade: capacidade da barra
    - solucao_inicial: lista de barras (cada barra é lista de itens)
    - max_iter: número máximo de iterações ILS (controle global)
    Retorna: (melhor_solucao, melhor_desperdicio, tempo_exec)
    """
    inicio_total = time.time()
    random.seed()  # comportamento estocástico
    
    # parâmetros internos
    max_iter_ls = 200       # iterações máximas da busca local interna por chamada
    max_no_improve_ls = 20  # critério de parada rápido da busca local
    perturb_k = 2           # número de itens a perturbar na etapa de shake
    max_iter_ils = max_iter if max_iter > 0 else 100

    def custo(sol):
        return calcular_desperdicio(capacidade, sol)

    # funções auxiliares (operam em cópias)
    def eliminar_barra(sol):
        """
        Tenta eliminar uma barra testando realocações em cópia.
        Retorna nova solução se alguma barra puder ser eliminada (primeira que der certo),
        caso contrário retorna sol (inalterada).
        """
        # ordenar barras por preenchimento crescente (tentar eliminar as menos cheias primeiro)
        indices = sorted(range(len(sol)), key=lambda i: sum(sol[i]))
        for idx in indices:
            barra = sol[idx]
            # T: cópia das outras barras
            T = [copy.deepcopy(sol[i]) for i in range(len(sol)) if i != idx]
            sucesso = True
            # Ordem dos itens: pode usar ordem decrescente para facilitar encaixe
            itens = sorted(barra, reverse=True)
            for item in itens:
                encaixou = False
                # tentar nas barras mais cheias primeiro (best-fit like)
                T.sort(key=lambda b: sum(b), reverse=True)
                for destino in T:
                    if sum(destino) + item <= capacidade:
                        destino.append(item)
                        encaixou = True
                        break
                if not encaixou:
                    sucesso = False
                    break
            if sucesso:
                # retornamos T (barra eliminada)
                return T
        return sol

    def realocar_item(sol):
        """
        One-item move: tenta mover um item de uma barra para outra se melhora custo.
        Retorna nova solução se encontrar movimento melhorante; caso contrário sol.
        """
        # iterar itens em barras (preferir itens grandes primeiro)
        # construir lista (barra_idx, item) ordenada por item descendente
        items_list = []
        for b_idx, barra in enumerate(sol):
            for item in barra:
                items_list.append((b_idx, item))
        # ordenar por tamanho decrescente
        items_list.sort(key=lambda x: x[1], reverse=True)
        for (b_idx, item) in items_list:
            for dest_idx in range(len(sol)):
                if dest_idx == b_idx:
                    continue
                if sum(sol[dest_idx]) + item <= capacidade:
                    T = [copy.deepcopy(s) for s in sol]
                    # remover item da origem (remove apenas uma ocorrência)
                    try:
                        T[b_idx].remove(item)
                    except ValueError:
                        continue  # item não está lá na cópia (pouco provável), pular
                    T[dest_idx].append(item)
                    # se barra origem ficou vazia, eliminá-la da solução
                    T = [b for b in T if b]  
                    if custo(T) < custo(sol):
                        return T
        return sol

    def swap_itens(sol):
        """
        Swap inteligente: testa troca entre pares de itens de barras distintas.
        Retorna solução melhorante se encontrada.
        """
        # percorrer pares de barras
        n = len(sol)
        # ordenar barras por soma para heurística (opcional)
        order = list(range(n))
        order.sort(key=lambda i: sum(sol[i]), reverse=True)
        for i_idx in range(n):
            for j_idx in range(i_idx+1, n):
                b1 = order[i_idx]
                b2 = order[j_idx]
                # testar swaps entre items das barras b1 e b2
                for item1 in sol[b1]:
                    for item2 in sol[b2]:
                        new_sum_b1 = sum(sol[b1]) - item1 + item2
                        new_sum_b2 = sum(sol[b2]) - item2 + item1
                        if new_sum_b1 <= capacidade and new_sum_b2 <= capacidade:
                            T = [copy.deepcopy(s) for s in sol]
                            # efetuar troca
                            try:
                                T[b1].remove(item1)
                                T[b2].remove(item2)
                            except ValueError:
                                continue
                            T[b1].append(item2)
                            T[b2].append(item1)
                            # remover barras vazias
                            T = [b for b in T if b]
                            if custo(T) < custo(sol):
                                return T
        return sol

    def busca_local_interna(sol):
        """
        Aplica iterativamente eliminar_barra, realocar_item e swap_itens até não melhorar.
        Usa limite de iterações max_iter_ls.
        """
        S = [copy.deepcopy(b) for b in sol]
        best = [copy.deepcopy(b) for b in S]
        best_cost = custo(best)
        no_improve = 0
        iter_ls = 0
        while iter_ls < max_iter_ls and no_improve < max_no_improve_ls:
            improved = False
            # 1) tentar eliminar barra
            S1 = eliminar_barra(S)
            if S1 is not S and custo(S1) < best_cost:
                S = [copy.deepcopy(b) for b in S1]
                best = [copy.deepcopy(b) for b in S]
                best_cost = custo(best)
                improved = True
                no_improve = 0
                iter_ls += 1
                continue

            # 2) one-item move
            S2 = realocar_item(S)
            if S2 is not S and custo(S2) < best_cost:
                S = [copy.deepcopy(b) for b in S2]
                best = [copy.deepcopy(b) for b in S]
                best_cost = custo(best)
                improved = True
                no_improve = 0
                iter_ls += 1
                continue

            # 3) swap itens
            S3 = swap_itens(S)
            if S3 is not S and custo(S3) < best_cost:
                S = [copy.deepcopy(b) for b in S3]
                best = [copy.deepcopy(b) for b in S]
                best_cost = custo(best)
                improved = True
                no_improve = 0
                iter_ls += 1
                continue

            # se chegou aqui, não houve melhoria nesta iteração
            if not improved:
                no_improve += 1
            iter_ls += 1

        return best

    def perturbar(sol, k=perturb_k):
        """
        Perturba solução removendo k itens aleatórios e reinserindo-os via FFD (first-fit decrescente).
        """
        T = [copy.deepcopy(b) for b in sol]
        all_items = []
        for b in T:
            all_items.extend(b)
        if not all_items:
            return T
        # escolher k itens distintos
        k = min(k, len(all_items))
        itens_escolhidos = random.sample(all_items, k)
        # remover as ocorrências selecionadas (uma por item escolhido)
        for item in itens_escolhidos:
            removed = False
            for b in T:
                if item in b:
                    b.remove(item)
                    removed = True
                    break
            # remover barras vazias
            T = [b for b in T if b]
        # reinsere os itens por ordem decrescente (FFD)
        itens_escolhidos.sort(reverse=True)
        for item in itens_escolhidos:
            placed = False
            # tentar first-fit
            for b in T:
                if sum(b) + item <= capacidade:
                    b.append(item)
                    placed = True
                    break
            if not placed:
                T.append([item])
        return T

    # --- início do ILS ---
    S0 = [copy.deepcopy(b) for b in solucao_inicial]
    # garantir consistência (remover barras vazias)
    S0 = [b for b in S0 if b]
    S0 = busca_local_interna(S0)
    best_solution = [copy.deepcopy(b) for b in S0]
    best_cost = custo(best_solution)

    current = [copy.deepcopy(b) for b in S0]

    iter_ils = 0
    while iter_ils < max_iter_ils:
        # perturba
        shaken = perturbar(current)
        # local search intensification
        shaken = busca_local_interna(shaken)
        shaken_cost = custo(shaken)

        # atualizar melhor global
        if shaken_cost < best_cost:
            best_solution = [copy.deepcopy(b) for b in shaken]
            best_cost = shaken_cost

        # critério de aceitação simples: aceitar se melhor ou igual, senão aceitar com pequena probabilidade
        if shaken_cost <= custo(current) or random.random() < 0.01:
            current = [copy.deepcopy(b) for b in shaken]
        else:
            current = [copy.deepcopy(b) for b in best_solution]

        iter_ils += 1

    tempo_total = time.time() - inicio_total
    return best_solution, best_cost, tempo_total


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