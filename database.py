import sqlite3

#Nome do arquivo que vai salvar os dados
DB_NAME = "cache_buscas.db"

def conectar():
    #cria e retorna uma conexão com o banco de dados SQLite
    return sqlite3.connect(DB_NAME)

def criar_tabelas():
    #cria as tabelas no banco de dados se elas ainda não existirem.
    conn = conectar()
    cursor = conn.cursor()

    #Tabela 1: Guarda qual
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Historico_Buscas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            termo_busca TEXT UNIQUE NOT NULL,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')


    #Tabela 2: Guarda os produtos encontrados para aquela busca
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Resultados_Temporarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        busca_id INTEGER NOT NULL,
        loja TEXT NOT NULL,
        titulo TEXT NOT NULL,
        preco REAL NOT NULL,
        link TEXT NOT NULL,
        em_estoque BOOLEAN NOT NULL,
        imagem_url TEXT,
        FOREIGN KEY (busca_id) REFERENCES Historico_Buscas (id)
    )
     ''')

    #salva as alterações e fecha a conexão
    conn.commit()
    conn.close()
    print("Banco de dados e tabelas verificados/criados com sucesso!")

#este bloco faz com que as tabelas sejam criadas se rodarmos este arquivo diretamente
if __name__ == "__main__":
    criar_tabelas()
