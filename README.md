SmartBuy B2B - Consultor de Preços API
🚀 Visão Geral
O SmartBuy B2B é uma aplicação Full-Stack (Backend + Frontend) desenvolvida para buscar, estruturar e apresentar preços de fornecedores. Esta versão de portfólio utiliza um motor de busca simulado (Mock) integrado a um sistema de cache real. Essa arquitetura garante resiliência, permitindo que a interface e o banco de dados sejam testados 100% do tempo sem interrupções por bloqueios de anti-bots (CAPTCHAs) comuns em e-commerces reais.

Principais Funcionalidades:

Motor Simulado: Retorno assíncrono de produtos estruturados em tempo real.

Sistema de Cache: Banco de dados integrado para evitar buscas repetidas e otimizar o tempo de resposta.

Frontend Integrado: Interface responsiva em HTML/JS consumindo a API diretamente.

🛠️ Tecnologias Utilizadas
Python 3 & FastAPI: Criação da API REST e rotas assíncronas de alta performance.

Pydantic: Validação rigorosa dos modelos de dados (Data Structuring).

SQLite: Banco de dados relacional leve atuando como Cache.

Uvicorn: Servidor web ASGI para rodar a aplicação.

⚙️ Como Executar o Projeto
Clone o repositório ou abra-o em seu GitHub Codespaces.

Instale as dependências listadas (FastAPI, Uvicorn, etc).

Inicie o servidor localmente rodando o comando:

uvicorn main:app --reload

Acesse [http://127.0.0.1:8000](http://127.0.0.1:8000) para visualizar a interface gráfica, ou adicione /docs ao final da URL para testar a API via Swagger UI.