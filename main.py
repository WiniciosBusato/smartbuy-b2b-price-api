import asyncio
import time
from typing import List, Optional
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
import database

# Força a criação das tabelas corretas toda vez que a API ligar
database.criar_tabelas()

# Pydantic valida os dados que entram e saem da API
class PrecoProduto(BaseModel):
    loja: str
    titulo: str
    preco: float
    link: HttpUrl
    em_estoque: bool
    imagem_url: Optional[str] = None

class RespostaBusca(BaseModel):
    termo: str
    resultado: List[PrecoProduto]
    tempo_execucao: float


# ==========================================
# 1. MOTOR SIMULADO (MOCK)
# ==========================================
async def buscar_preco_simulado(termo: str) -> Optional[PrecoProduto]:
    """
    Função que simula uma busca na internet. 
    Excelente para portfólios e entrevistas, pois nunca quebra por causa de anti-bots.
    """
    # Simulamos o atraso de rede (1.5 segundos para parecer real)
    await asyncio.sleep(1.5)
    
    print(f"🤖 Gerando dados simulados profissionais para: {termo}")
    
    # Devolvemos um produto de demonstração com cara de profissional
    return PrecoProduto(
        loja="Fornecedor Premium B2B",
        titulo=f"{termo.capitalize()} - Lote Atacado (Caixa com 12)",
        preco=149.90,
        link="https://exemplo.com/produto-simulado",
        em_estoque=True,
        imagem_url="https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=300&auto=format&fit=crop&q=60"
    )


# ==========================================
# 2. CÉREBRO (BANCO DE DADOS / CACHE)
# ==========================================
def salvar_no_cache(termo: str, resultados: List[PrecoProduto]):
    '''Salva a busca e os produtos encontrados no banco de dados.'''
    conn = database.conectar()
    cursor = conn.cursor()

    # Salva o termo na tabela Historico_Buscas
    cursor.execute("INSERT OR REPLACE INTO Historico_Buscas (termo_busca) VALUES (?)", (termo.lower(),))
    busca_id = cursor.lastrowid

    # Salva cada produto na tabela Resultados_Temporarios atrelado ao ID da busca
    for item in resultados:
        cursor.execute('''
        INSERT INTO Resultados_Temporarios
        (busca_id, loja, titulo, preco, link, em_estoque, imagem_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (busca_id, item.loja, item.titulo, item.preco, str(item.link), item.em_estoque, item.imagem_url))
    
    conn.commit()
    conn.close()

def buscar_no_cache(termo: str) -> Optional[List[PrecoProduto]]:
    '''Procura no banco se esse termo já foi pesquisado antes.'''
    conn = database.conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM Historico_Buscas WHERE termo_busca = ?", (termo.lower(),))
    busca = cursor.fetchone()

    if busca:
        busca_id = busca[0]
        cursor.execute('''
        SELECT loja, titulo, preco, link, em_estoque, imagem_url
        FROM Resultados_Temporarios WHERE busca_id = ?
        ''', (busca_id,))

        linhas = cursor.fetchall()
        resultados_salvos = []
        for linha in linhas:
            produto = PrecoProduto(
                loja=linha[0],
                titulo=linha[1],
                preco=linha[2],
                link=linha[3],
                em_estoque=bool(linha[4]),
                imagem_url=linha[5]
            )
            resultados_salvos.append(produto)
        
        conn.close()
        return resultados_salvos

    conn.close()
    return None


# ==========================================
# 3. APLICAÇÃO FASTAPI (ROTAS)
# ==========================================
app = FastAPI(
    title="SmartBuy B2B Price API",
    description="Backend de meta-busca de preços (Versão Mock/Demonstração).",
    version="1.0.0"
)

@app.get("/api/busca", response_model=RespostaBusca)
async def realizar_busca(q: str):
    inicio = time.time()
    
    # Passo A: Tenta buscar no Banco de Dados
    resultados_cacheados = buscar_no_cache(q)
    if resultados_cacheados:
        tempo = time.time() - inicio
        print("🚀 Retornando dados ultra-rápidos do Banco de Dados!")
        return RespostaBusca(termo=q, resultado=resultados_cacheados, tempo_execucao=tempo)
        
    # Passo B: Se não tem no banco, usa nosso motor simulado
    print("🔍 Buscando dados no fornecedor parceiro...")
    resultado_simulado = await buscar_preco_simulado(q)
    
    # Passo C: Valida e salva no cache
    resultados_validos = [resultado_simulado] if resultado_simulado else []
    if resultados_validos:
        salvar_no_cache(q, resultados_validos)
    
    tempo = time.time() - inicio
    return RespostaBusca(termo=q, resultado=resultados_validos, tempo_execucao=tempo)

@app.get("/")
async def pagina_inicial():
    return FileResponse("index.html")