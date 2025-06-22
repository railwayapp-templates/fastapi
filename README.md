---
title: FastAPI
description: A FastAPI server
tags:
  - fastapi
  - hypercorn
  - python
---

# FastAPI - API de Datas Indisponíveis

![Testes](https://github.com/wellington-faria/fastapi/workflows/Testes%20API%20FastAPI/badge.svg)

Uma API FastAPI que coleta e consolida datas indisponíveis de múltiplas plataformas de reserva (Booking, VRBO, Holmy, Airbnb) através de seus calendários iCal.

## 🚀 Funcionalidades

- **Endpoint raiz (`/`)**: Retorna uma mensagem de boas-vindas
- **Endpoint de datas (`/datas-indisponiveis`)**: Coleta e retorna todas as datas indisponíveis das plataformas configuradas

## 📋 Pré-requisitos

- Python 3.9+
- pip

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone <seu-repositorio>
cd fastapi
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 🚀 Executando a aplicação

### Desenvolvimento local
```bash
# Usando FastAPI diretamente
uvicorn main:app --reload

# Ou usando Hypercorn (configurado no projeto)
hypercorn main:app --reload
```

A API estará disponível em `http://localhost:8000`

### Documentação interativa
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Executando os testes

### Testes locais
```bash
# Executar testes diretamente
python test_main.py

# Ou usando pytest
pytest test_main.py -v
```

### Testes automatizados (GitHub Actions)

Os testes são executados automaticamente via GitHub Actions em:
- **Push** para as branches `main` e `develop`
- **Pull Requests** para a branch `main`

O workflow executa:
- ✅ Testes em múltiplas versões do Python (3.9, 3.10, 3.11)
- ✅ Verificação de sintaxe
- ✅ Linting com flake8
- ✅ Cache de dependências para otimização

## 📁 Estrutura do projeto

```
fastapi/
├── .github/
│   └── workflows/
│       └── test.yml          # Configuração GitHub Actions
├── main.py                   # Aplicação FastAPI principal
├── test_main.py             # Testes da API
├── requirements.txt         # Dependências Python
├── railway.json             # Configuração Railway
├── README.md               # Este arquivo
└── LICENSE.md              # Licença
```

## 🔌 Endpoints da API

### GET `/`
Retorna mensagem de boas-vindas.

**Resposta:**
```json
{
  "greeting": "Hello, World!",
  "message": "Welcome to FastAPI!"
}
```

### GET `/datas-indisponiveis`
Coleta e retorna datas indisponíveis de todas as plataformas configuradas.

**Resposta de sucesso:**
```json
{
  "datas_indisponiveis": [
    "01/12/2023",
    "02/12/2023",
    "15/12/2023"
  ]
}
```

**Resposta de erro:**
```json
{
  "error": "Erro ao processar [plataforma]: [detalhes do erro]"
}
```

## 🏗️ Plataformas integradas

- **Booking.com**: Calendário iCal
- **VRBO**: Calendário iCal  
- **Holmy**: Calendário iCal
- **Airbnb**: Calendário iCal

## 📦 Dependências principais

- `fastapi==0.100.0` - Framework web
- `hypercorn==0.14.4` - Servidor ASGI
- `icalendar==5.0.11` - Parser de calendários iCal
- `requests==2.31.0` - Cliente HTTP
- `pytest==7.4.0` - Framework de testes

## 🔄 CI/CD

O projeto usa GitHub Actions para:
- Executar testes automaticamente
- Verificar qualidade do código
- Suportar múltiplas versões do Python
- Cache de dependências para builds mais rápidos

## 📝 Licença

Este projeto está sob a licença definida no arquivo LICENSE.md.
