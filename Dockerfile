# --- STAGE 1: Python Dependencies ---
FROM python:3.11-slim-bookworm AS python-deps

# Instala dependências de sistema necessárias para algumas bibliotecas Python
# (ex: Pillow, psycopg2-binary, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    # As libs para PyUSB/escpos continuam sendo um desafio em containers para acesso direto ao hardware.
    # Se você realmente precisar de acesso a hardware, precisará de uma solução mais complexa.
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências Python
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

---

# --- STAGE 2: Final Application Image ---
FROM python:3.11-slim-bookworm

# Define o diretório de trabalho
WORKDIR /app

# Copia as dependências Python do estágio anterior
COPY --from=python-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Copia todo o código fonte da sua aplicação
# Certifique-se de que o .dockerignore esteja configurado para ignorar venv, .git, etc.
COPY . .

# Coleta os arquivos estáticos do Django
# Certifique-se de que STATIC_ROOT no seu settings.py está configurado corretamente,
# por exemplo, para `/app/staticfiles`.
RUN python manage.py collectstatic --noinput

# Expõe a porta que o Gunicorn vai usar
EXPOSE 8000

# Comando para iniciar o Gunicorn (servidor de aplicação Django)
# 'core.wsgi:application' assume que seu arquivo wsgi.py está em 'core/wsgi.py'
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]