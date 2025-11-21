# Admin Auth Server

Este diretório contém o código Python para rodar o serviço de alteração de senha do admin em uma VPS (Digital Ocean, AWS, etc).

## Pré-requisitos

- Python 3.8+
- Pip
- Acesso ao projeto Supabase (URL e Service Role Key)

## Configuração

1. **Crie um ambiente virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure as variáveis de ambiente:**
   Crie um arquivo `.env` na mesma pasta com o seguinte conteúdo:
   ```env
   SUPABASE_URL=seu_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=sua_service_role_key_secreta
   ```
   > **Atenção:** Use a `service_role_key`, não a `anon_key`, pois é necessário permissão para atualizar a tabela `admin_users`.

## Executando o Servidor

Para desenvolvimento:
```bash
uvicorn server:app --reload
```

Para produção (exemplo com Gunicorn):
```bash
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## Configuração no Frontend

No projeto React, atualize a variável de ambiente `VITE_VPS_API_URL` para apontar para o IP/domínio da sua VPS.

Exemplo no `.env` do frontend:
```
VITE_VPS_API_URL=http://seu-ip-da-vps:8000
```

# i9solar-backend
