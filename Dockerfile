# Dofus Touch Calculator — Image Docker
#
# Prérequis pour utiliser l'interface graphique depuis Docker :
#   Linux : xhost +local:docker && docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix dofus-calculator
#   macOS : installer XQuartz, puis xhost + et exporter DISPLAY=host.docker.internal:0
#   Windows : installer VcXsrv ou Xming, puis utiliser DISPLAY=host.docker.internal:0.0

FROM python:3.11-slim

# Dépendances système nécessaires à tkinter et PIL
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    tk-dev \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Les données utilisateur sont stockées dans /app/data — monter un volume pour les persister :
#   docker run -v ./data:/app/data ...
VOLUME ["/app/data"]

ENV DISPLAY=:0

CMD ["python", "DofusCalculator.py"]
