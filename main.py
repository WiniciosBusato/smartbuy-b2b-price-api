#importações
import asyncio
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
import json
from fastapi import FastAPI, Query
from pydantic import BaseModel, HttpUrl
import database

#Pydantic valida os dados que entram e saem da API
class PrecoProduto(BaseModel):
    loja:str
    titulo:str
    preco:float
    link:HttpUrl
    em_estoque:bool
    imagem_url:Optional[str] = None

class RespotaBusca(BaseModel):
    termo:str
    resultado: List[PrecoProduto]
    tempo_execucao:float

async def estrair_dados_json_ld(html_content: str, url: str, nome_loja: str) -> Optional[PrecoProduto]:
    '''
    Função auxiliar para varrer o HTML em busca  de dados  estruturados (JSON-LD).
    Isso evita quebras constantes por mudança de layout visual.
    '''
    try:
        soup = BeatifulSoup(html_content, "html.parser")
        #Procura por scripts do tipo application/ld+json
        scripts = soup.find_all("script", type="application/ld+json")

        for script in scripts:
            try:
                data = json.loads(script.string)
                # O JSON-LD pode ser um objeto unico ou uma lista de objetos
                if data.get(deta, dict):
                    #Procura por esquemas do tipo "Product" dentro de um "@graph"
                    if data.get("@type") == "Product":
                        nome = data.get("name"),
                        offers = data.get("offers", {})

                        #extrai preço e disponibilidade
                        preco = 0.0
                        disponivel = False

                        if isinstance(offers, dict):
                            preco = float(offers.get("price", 0))
                            dispo_str = offers.get("availability", "")
                            disponivel = "InStock" in dispo_str or "preOrder" in dispo_str
                        elif isinstance(offers, list) and len (offers) > 0:
                            preco = float(offers[0].get("price", 0))
                            dispo_str = offers[0].get("availability", "")
                            disponivel = "InStock" in dispo_str

                        return PrecoProduto(
                            loja=nome_loja,
                            titulo=nome or "Produto sem nome",
                            preco=preco,
                            link=url,
                            em_estoque=disponivel,
                            imagem_url=data.get("image")
                        )
            except (json.JSONecodeError, TypeError, ValueError):
                continue
    except Exception as e:
        print(f"Erro ao processar JSON-LD para {nome_loja}: {0}")
    return None

async def buscar_fornecedor_mock(client: httpx.AsyncClient, loja: str, termo: str) -> Optional[PrecoProduto]:
    '''
    Simula uma requisição assincrona. Em produção, aqui sera feito o fetch real do HTML
    ou a chamada da API oficial da loja.
    '''
    #Simulando delay de rede variavel (entre 300ms e 900ms)
    await asyncio.sleep(0.3 + (asyncio.get_event_loop().time() % 0.6))

    #Criando dados ficticios para simular a resposta de busca do forcenedor
    precos_mock = {
        "Amazon": 34.90,
        "Mercado Livre": 29.90,
        "MAgazine Luiza": 32.50 
    }

    preco = precos_mock.get(loja, 30.0)
    #Adiciona uma pequena variação baseada no tamanho do termo buscado para não ficar estático
    preco += len(termo) *0.1

    return PrecoProduto(
        loja=loja,
        titulo=f"{termo.title()} - oferta{loja}",
        preco=round(preco, 2),
        link=f"https://www.{loja.lower().replace(' ','')}.com.br/s?q={termo}",
        em_estoque=True,
        imagem_url="https://placehold.co/150x150/efefef/333333?text=Produto"
    )

def salvar_no_cache(termo: str, resultados: str):
    '''Salva a busca e os produtos encontrados no banco de dados.'''
    conn = database.conectar()
    cursor = conn.cursor()

    #1- Salva o termo na tabela Historico_Buscas
    cursor.execute("INSERT INTO Historico_Buscas (termo_busca) VALUES (?)", (termo.lower(),))
    busca_id = cursor.lastrowid #ega o ID gerado para essa busca

    #2- Salva cada produto na tabela Resultados_Temporarios atrelado ao ID da busca
    for item in resultados:
        cursor.execute('''
        INSERT INTO Resultado_Temporarios
        (busca_id, loja, titulo, preco, link, em_estoque, imagem_url)
        VALUES (?, ?, ?, ?, ?, ?, ?,)
        ''', (busca_id, item.loja, item.titulo, item.preso, str(item.link), item.em_estoque, item.imagem_url))
    
    conn.commit()
    conn.close()

def buscar_no_cache(termo: str) -> Optional[List[PrecoProduto]]:
    '''Procura no banco se esse termo já foi pesquisado antes.'''
    conn = database.conectar()
    cursor = conn.cursor()

    # tenta achar o ID da busca usando o termo
    cursor.execute("SELECT id FROM Historico_Buscas WHERE termo_busca = ?", (termo.lower(),))
    busca = cursor.fetchone()

    #Se a busca existir, os prdutos serão pegos
    if busca:
        busca_id = busca[0]
        cursor.execute('''
        SELECT loja, titulo, preco, link, em_estoque, imagem_url
        FROM Resultados_Temporarios WHERE busca_id = ?
        ''', (busca_id))

        linhas = cursor.fetchall()

        #reconstroi os resultados no formato que a API exige
        resultados_salvos =[]
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

    #se não achar nada, retorna vazio
    conn.close()
    return None

app = FastAPI(
    title="SmartBuy B2B Price API",
    description="Backend de meta-busca assíncrona de preços em tempo real para múltiplos fornecedores.",
    version="1.0.0"
)

@app.get("/api/busca", response_model=RespotaBusca)
async def realizar_busca(q: str = Query(..., min_length=2, description="Termo de pesquisa")):
    #inicia o cronometro
    tempo_inicial = asyncio.get_event_loop().time()

    #1- Tenta buscar no DB primeiro
    resultados_cacheados = buscar_no_cache(q)

    if resultados_cacheados:
        print("Retornando dados ultra-rápidos do Banco de Dados")
        tempo_execucao = asyncio.get.get_event_loop().time() - tempo_inicial
        return RespotaBusca(
            termo=q,
            resultado=resultados_cacheados,
            tempo_execucao=tempo_execucao
        )
    #2- Se não tem no DB, faz a busca "real" na NET
    print("Buscando dados novos na internet...")
    fornecedores = ["Amazon","Mercado livre","Magazine Luiza"]

    async with httpx.AsyncClient() as client:
        #prepara todas as tarefas para rodar ao mesmo tempo
        tarefas = [buscar_fornecedor_mock(client, loja, q) for loja in fornecedores]
        #Dispara todas de uma vez
        resultados = await asyncio.gather(*tarefas)
    
    #limpa a lista removendo valores vazios (caso algum site tenha falhado)

#FIM DA MODIFICAÇÃO
@app.get("/")
def home():
    return {"status": "Online", "message": "SmartBuy API rodando com sucesso. Acesso /docs para testar as rotas de busca!"}

        