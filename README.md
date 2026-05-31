# RADCoringa - Sistema de Gestão de Autenticação Radius

Sistema web para gerenciamento de clientes e autenticação RADIUS, automatizando o cadastro de usuários e autenticação com RADIUS (RAdm). 

##  Instalação e Execução com Docker

O projeto utiliza Docker Compose para facilitar a implantação. Siga os passos abaixo para configurar e executar o sistema:

### Pré-requisitos

- [Docker](https://www.docker.com/get-started/)
- [Git](https://git-scm.com/)
- [uv](https://github.com/astral-sh/uv)

### 1. Clonar o repositório
```bash
git clone https://github.com/EmersonComar/radcoringa.git
cd radcoringa
```

### 2. Configurar variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:
```bash
cp .env.example .env
```

Edite o arquivo `.env` com as configurações do seu ambiente.


### 3. Executar com Docker Compose
```bash
docker-compose up -d --build
```

### 4. Sincronizar dependencias
```bash
uv sync
```

### 5. Executar migrações
```bash
uv run python manage.py migrate
```

### 6. Criar superusuário
```bash
uv run python manage.py createsuperuser
```

### 7. Executar servidor de desenvolvimento
```bash
uv run python manage.py runserver
```

## Script para subir o ambiente
Crie um arquivo `setup.sh` na raiz do projeto:
```bash
#!/bin/bash



docker-compose up -d --build
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
```