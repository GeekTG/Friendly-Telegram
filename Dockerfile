#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

FROM python:3.8-slim-buster
ENV PIP_NO_CACHE_DIR=1
COPY requirements.txt /app/requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libcairo2 \
    git \
    && rm -rf /var/lib/apt/lists /var/cache/apt/archives /tmp \
    && pip install --no-warn-script-location -r /app/requirements.txt

COPY friendly-telegram/ /app/friendly-telegram
COPY web-resources/ /app/web-resources

WORKDIR /app
RUN [ "python", "-m", "friendly-telegram", "--no-web", "--no-auth", "--docker-deps-internal", "--data-root", "/data" ]

ENV PORT=8080
EXPOSE $PORT
ENTRYPOINT [ "python", "-m", "friendly-telegram", "--data-root", "/data" ]
