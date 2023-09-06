FROM python:3.11.5-slim-bullseye

# Instala dependências
COPY requirements.txt /srv/requirements.txt
RUN pip install -r /srv/requirements.txt

# Copia arquivo
COPY . /srv

CMD ["python", "/srv/main.py"]
