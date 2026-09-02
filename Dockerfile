FROM node:22-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1     BGUTIL_SERVER_HOME=/opt/bgutil-ytdlp-pot-provider/server     CONVERTNEST_DISABLE_LOCAL_POT=1     YTDL_POT_PROVIDER_URL=http://127.0.0.1:4416     CONVERTNEST_USE_POT_HTTP=1

RUN apt-get update     && apt-get install -y --no-install-recommends python3 python3-pip ffmpeg git ca-certificates curl build-essential     && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt

RUN git clone --depth 1 --branch 1.3.2 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /opt/bgutil-ytdlp-pot-provider     && cd /opt/bgutil-ytdlp-pot-provider/server     && npm ci     && npx tsc

COPY . .

RUN chmod +x /app/start.sh

EXPOSE 8000
CMD ["/app/start.sh"]
