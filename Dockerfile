# Use intermediate to reduce final image size
FROM alpine/git AS builder
ARG SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.33/supercronic-linux-amd64
WORKDIR /app

# Get androidtvbackground app:
RUN git clone -q https://github.com/adelatour11/androidtvbackground.git . && \
    rm -rf .git
# Use supercronic instead of cron for better container support
ADD ${SUPERCRONIC_URL} supercronic
# Add font
ADD https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf Roboto-Light.ttf

# Create main image
FROM python:3.11.11-slim
ARG VERSION
ARG SUPERCRONIC_SHA1SUM=71b0d58cc53f6bd72cf2f293e09e294b79c666d8
LABEL org.opencontainers.image.source="https://github.com/ninthwalker/androidtvbackground-docker" \
      org.opencontainers.image.description="Create background wallpapers from Plex/TMDB/Trakt" \
      org.opencontainers.image.authors="ninthwalker" \
      org.opencontainers.image.version=$VERSION

# Set volume and copy files
VOLUME /config
VOLUME /backgrounds
COPY --from=builder /app /app
COPY . /

# Create default user
RUN groupmod -g 1000 users && \
    useradd -r -u 99 -U -s /usr/sbin/nologin xyz && \
    groupmod -o -g 100 xyz && \
    # Setup env and install deps
    mv /app/supercronic /supercronic && \
    echo "${SUPERCRONIC_SHA1SUM} /supercronic" | sha1sum -c - && \
    apt-get -qq update && \
    pip -qq install --no-cache-dir -r /app/requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache/pip && \
    # Update perms
    chown -R xyz:xyz /app entrypoint.sh run.sh supercronic && \
    chmod -R ug=rw,o=r,a-x+X /app && \
    chmod +x entrypoint.sh run.sh supercronic

# Set entrypoint & CMD
USER xyz
ENTRYPOINT ["/entrypoint.sh"]
CMD ["./supercronic", "-quiet", "/app/cron"]
