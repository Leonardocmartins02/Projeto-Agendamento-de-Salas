# 🏫 Sistema de Agendamento de Salas

Aplicação web para gerenciar reservas de salas em uma universidade. Backend em Flask + SQLite/SQLAlchemy e frontend leve com HTML, CSS e JavaScript.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-TBD-lightgrey.svg)](#-licença)
[![Status](https://img.shields.io/badge/Status-MVP-green.svg)](#-roadmap--versões)

---

## 📌 Sumário

- [Visão Geral](#-visão-geral)
- [Arquitetura e Stack](#-arquitetura-e-stack)
- [Como Rodar](#-como-rodar)
- [Como Usar](#-como-usar)
- [Referência da API](#-referência-da-api)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Decisões e Desafios](#-decisões-e-desafios)
- [Troubleshooting](#-troubleshooting)
- [Roadmap / Versões](#-roadmap--versões)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

---

## ✨ Visão Geral

- Sistema para listar salas, visualizar agendamentos e realizar CRUD de reservas.
- Validação de conflitos de horários no backend.
- UI com feedback acessível (toasts e `aria-live`) e suporte a busca com acentos.
- Rotas REST simples e interface servida pelo próprio Flask.

Arquivos principais:
- Backend: [app.py](cci:7://file:///home/leonardo/projeto_final/app.py:0:0-0:0)
- Template: [templates/index.html](cci:7://file:///home/leonardo/projeto_final/templates/index.html:0:0-0:0)
- Estáticos: [static/css/style.css](cci:7://file:///home/leonardo/projeto_final/static/css/style.css:0:0-0:0), [static/js/script.js](cci:7://file:///home/leonardo/projeto_final/static/js/script.js:0:0-0:0), `static/images/`

---

## 🧱 Arquitetura e Stack

- Backend: `Flask`
- Banco local: `SQLite` via `SQLAlchemy`
- CORS: `Flask-Cors`
- Frontend: HTML + CSS + JS puro (sem framework)
- Acessibilidade: `aria-live`, foco visível, navegação por teclado
- Design: tokens CSS, dark mode via `prefers-color-scheme`, componentes (listas, badges, toasts)

Modelos ([app.py](cci:7://file:///home/leonardo/projeto_final/app.py:0:0-0:0)):
- [Sala(id, nome, capacidade)](cci:2://file:///home/leonardo/projeto_final/app.py:14:0-19:80)
- [Agendamento(id, sala_id, responsavel, data_inicio, data_fim)](cci:2://file:///home/leonardo/projeto_final/app.py:21:0-28:172)

---

## 🚀 Como Rodar

Pré-requisitos:
- Python 3.10+ (testado com 3.12)
- `pip`
- Ambiente virtual (recomendado)

Passo a passo:
1) Criar e ativar o ambiente virtual
   - Linux/macOS:
     - python3 -m venv venv
     - source venv/bin/activate
   - Windows (PowerShell):
     - python -m venv venv
     - venv\Scripts\Activate.ps1

2) Instalar dependências
   - pip install -r requirements.txt
   - Para rodar os testes também: pip install -r requirements-dev.txt

3) Rodar o servidor (modo desenvolvimento)
   - python app.py

4) Abrir o navegador e acessar
   - http://127.0.0.1:5000

Observações:
- Ao iniciar, o app cria automaticamente o banco SQLite `agendamentos.db` e popula 3 salas exemplo (ver [app.py](cci:7://file:///home/leonardo/projeto_final/app.py:0:0-0:0)).
- CORS está habilitado para permitir requests do frontend servido pelo Flask.

---

## 🧪 Testes

Testes funcionais (pytest + Flask `test_client`), cada teste roda contra um banco SQLite temporário isolado:

```
pip install -r requirements-dev.txt
pytest
```

Rodar um teste específico:
```
pytest tests/test_agendamentos.py::TestCriacao::test_bloqueia_conflito_de_horario
```

Cobertura atual: criação/edição/exclusão de agendamentos, validação de payload inválido (sem quebrar com 500), conflito de horário em `POST` e `PUT`, e um teste de concorrência (`TestConcorrencia`) que dispara duas criações simultâneas no mesmo horário e garante que só uma vence (regressão para double-booking).


---

## 🧭 Como Usar

Na interface principal (`/`):
- Coluna esquerda: lista de salas.
  - Use o campo “Buscar sala…” para filtrar por nome (busca sem acentos, ex.: “Anfi pro” encontra “Anfiteatro Principal”).
  - Selecione uma sala para ver seus agendamentos.
- Coluna direita: agendamentos da sala selecionada + formulário.
  - “Horários Agendados”: lista com editar/excluir.
  - “Novo Agendamento”: preencha Nome, Início e Fim (formato `datetime-local`) e clique em “Agendar”.
  - Para editar, clique em “Editar” ao lado do item, altere dados e “Salvar Alterações”. “Cancelar Edição” volta ao modo criação.
- Acessibilidade: mensagens emergentes via região `aria-live` e toasts visuais no canto da tela.


---

## 📡 Referência da API (explicado do meu jeitinho)

Base URL: `http://127.0.0.1:5000`

- GET `/salas`
  - O que faz: lista todas as salas cadastradas.
  - Resposta (exemplo):
    [
      {"id": 1, "nome": "Anfiteatro Principal", "capacidade": 30},
      {"id": 2, "nome": "Laboratório de Projetos", "capacidade": 15}
    ]

- GET `/salas/<sala_id>/agendamentos`
  - O que faz: mostra os agendamentos daquela sala.
  - Resposta (exemplo):
    [
      {
        "id": 1,
        "sala_id": 1,
        "responsavel": "Maria",
        "data_inicio": "2025-09-08T09:00:00",
        "data_fim": "2025-09-08T10:00:00"
      }
    ]

- GET `/agendamentos`
  - O que faz: lista todos os agendamentos (de todas as salas).

- POST `/agendamentos`
  - O que faz: cria um novo agendamento.
  - Enviar no corpo (JSON):
    {
      "sala_id": 1,
      "responsavel": "Seu Nome",
      "data_inicio": "2025-09-08T09:00",
      "data_fim": "2025-09-08T10:00"
    }
  - Regras importantes:
    - `data_fim` precisa ser depois de `data_inicio` (senão dá erro 400).
    - Se bater o horário com outro agendamento da mesma sala, o backend bloqueia (erro 409).

- PUT `/agendamentos/<id>`
  - O que faz: atualiza um agendamento existente.
  - Enviar o JSON no mesmo formato do POST.

- DELETE `/agendamentos/<id>`
  - O que faz: apaga um agendamento.

Dicas:
- Eu testei com o navegador e também dá para usar Postman/Insomnia.
- Se preferir terminal, dá para usar `curl` básico:
  - Listar salas:
    curl http://127.0.0.1:5000/salas
  - Criar agendamento:
    curl -X POST http://127.0.0.1:5000/agendamentos \
      -H "Content-Type: application/json" \
      -d '{"sala_id":1,"responsavel":"Maria","data_inicio":"2025-09-08T09:00","data_fim":"2025-09-08T10:00"}'

Observação:
- Tentei manter as rotas bem diretas para eu mesmo entender fácil.
- Os horários são strings no padrão ISO (o Python entende com `fromisoformat`).


---

## 🗂️ Estrutura do Projeto (bem simples, é meu primeiro)

Árvore do projeto:
.
├── app.py
├── .gitignore
├── templates/
│   └── index.html
└── static/
    ├── css/
    │   └── style.css
    ├── js/
    │   └── script.js
    └── images/
        └── fundo-universidade.jpg

O que cada um faz :
- [app.py](cci:7://file:///home/leonardo/projeto_final/app.py:0:0-0:0)
  - É o coração do backend (Flask).
  - Cria o banco SQLite, define os modelos [Sala](cci:2://file:///home/leonardo/projeto_final/app.py:14:0-19:80) e [Agendamento](cci:2://file:///home/leonardo/projeto_final/app.py:21:0-28:172) e expõe as rotas da API.
  - Quando roda a primeira vez, ele já coloca 3 salas de exemplo para facilitar meus testes.

- [templates/index.html](cci:7://file:///home/leonardo/projeto_final/templates/index.html:0:0-0:0)
  - É a página única do frontend.
  - Tem duas colunas: lista de salas e, quando escolho uma sala, aparecem os agendamentos e o formulário.

- [static/js/script.js](cci:7://file:///home/leonardo/projeto_final/static/js/script.js:0:0-0:0)
  - É o JavaScript que busca dados do backend e atualiza a tela.
  - Fiz uma busca que ignora acentos e um “toast” simples para mensagens de sucesso/erro.
  - Ainda é código direto (sem framework), para eu aprender o básico.

- [static/css/style.css](cci:7://file:///home/leonardo/projeto_final/static/css/style.css:0:0-0:0)
  - Deixa a interface mais bonitinha.
  - Tem variáveis de cor, suporte a dark mode e alguns estilos para listas e botões.

- `static/images/fundo-universidade.jpg`
  - Imagem de fundo só para dar um clima.

- [.gitignore](cci:7://file:///home/leonardo/projeto_final/.gitignore:0:0-0:0)
  - Para não versionar coisas desnecessárias (como o virtualenv e arquivos gerados).
  - Ainda estou aprendendo o que colocar aqui.

Observação:
- Preferi começar simples, com HTML/CSS/JS puro, para entender bem a base.
- Sei que dá para organizar melhor e separar mais coisas, mas por enquanto está objetivo e eu consigo manter.

---

## 🧠 Decisões e Desafios

- Validação de conflito no backend:
  - Regra: há conflito se (inicio_novo < fim_existente) e (fim_novo > inicio_existente).
  - Implementado em `POST /agendamentos` com 409 em caso de choque.
- Datas no padrão ISO:
  - Front envia `datetime-local` (YYYY-MM-DDTHH:mm).
  - Backend usa `datetime.fromisoformat`.
- Acessibilidade:
  - `aria-live` para mensagens progressivas.
  - Foco visível (`:focus-visible`) e navegação por teclado na lista.
- UX e performance:
  - Busca com normalização ([normalizeText](cci:1://file:///home/leonardo/projeto_final/static/js/script.js:35:0-43:1)) para tolerar acentos.
  - Debounce no filtro de salas.
- Persistência simples:
  - SQLite via SQLAlchemy, com seed inicial de salas quando o DB está vazio.


---

## 🧩 Troubleshooting

- Erro CORS ou fetch bloqueado:
  - Certifique-se que o app Flask está em `http://127.0.0.1:5000` (CORS habilitado via `Flask-Cors`).
- Datas inválidas / formatos:
  - Envie `YYYY-MM-DDTHH:mm` no JSON. O backend rejeita `data_fim <= data_inicio` (400).
- Conflito de horário (409):
  - Ajuste o período. O backend impede sobreposição por sala.
- Banco “travado” (SQLite locked):
  - Feche processos que usam o arquivo `agendamentos.db`.
  - Pare e reinicie o servidor.
- Resetar banco de dados:
  - Pare o servidor.
  - Remova o arquivo `agendamentos.db` na raiz do projeto.
  - Inicie novamente para recriar o schema e os seeds.
- Porta já em uso:
  - Ex: FLASK_RUN_PORT=5001 python app.py (ou ajuste o `app.run(port=5001)`).


---

## 🗺️ Roadmap / Versões

- MVP (atual):
  - Listar salas, CRUD de agendamentos, validação de conflito, UI acessível.
- Próximas versões:
  - v1.1: Paginação/ordenar agendamentos e máscaras de data.
  - v1.2: Autenticação simples (responsável logado).
  - v1.3: Export/print da agenda da sala e iCal.
  - v1.4: Bloqueio de janela de manutenção (feriados).
  - v2.0: Multi-usuário com papéis e aprovação de reservas.


---

## 🤝 Contribuição

- Fork, branch por feature, PR com descrição clara.
- Padrão de commit simples (ex.: feat, fix, refactor, docs).
- Testes manuais via UI e `curl`/Insomnia.
- Sugerido: abrir issue antes para discutir mudanças maiores.


---

## 📄 Licença

- TBD. Definir licença aberta (ex.: MIT) ou política interna.
