FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends git ffmpeg curl unzip && \
    rm -rf /var/lib/apt/lists/* && \
    curl -fsSL https://deno.land/install.sh | sh && \
    ln -s /root/.deno/bin/deno /usr/local/bin/deno

WORKDIR /app
COPY requirements.txt .

# 🔥 FIX ENV (pip + yt-dlp)
RUN rm -rf /usr/local/lib/python3.12/site-packages/-wh-pip* && \
    python3 -m pip install --upgrade --force-reinstall pip && \
    pip uninstall yt-dlp -y || true && \
    pip install --no-cache-dir yt-dlp==2026.3.17 && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "-m", "AnnieXMedia"]
