#    Friendly Telegram Userbot
#    by GeekTG Team

FROM python:3.8-slim-buster as main
ENV PIP_NO_CACHE_DIR=1
COPY requirements.txt /app/requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libcairo2 \
    git \
    neofetch \
    && rm -rf /var/lib/apt/lists /var/cache/apt/archives /tmp \
    && pip install --no-warn-script-location --no-cache-dir -r /app/requirements.txt cryptg \
# The next line is used to ensure that /data exists. It won't exist if we are running in a CI job.
    && mkdir -p /data

COPY friendly-telegram/ /app/friendly-telegram
COPY web-resources/ /app/web-resources

WORKDIR /app
RUN [ "python", "-Om", "friendly-telegram", "--no-web", "--no-auth", "--docker-deps-internal", "--data-root", "/data" ]

STOPSIGNAL SIGINT

COPY healthcheck.py /app/healthcheck.py
HEALTHCHECK CMD [ "python", "-O", "/app/healthcheck.py" ]

ENV PORT=8080
EXPOSE $PORT
ENTRYPOINT [ "python", "-Om", "friendly-telegram", "--data-root", "/data" ]

FROM main as test
COPY test-requirements.txt .
RUN pip install --no-warn-script-location -r test-requirements.txt

COPY tox.ini .
COPY test.sh .

ENTRYPOINT [ "bash", "test.sh" ]
