# Usar uma imagem base com Python
FROM python:3.9-slim

# Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar o arquivo requirements.txt para dentro do contêiner
COPY requirements.txt /app/

# Instalar as dependências necessárias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código da aplicação para o contêiner
COPY . /app/

# Expôr a porta que a aplicação vai rodar
EXPOSE 8002

# Comando para rodar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
