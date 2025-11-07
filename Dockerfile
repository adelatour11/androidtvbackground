# Use intermediate to reduce final image size
FROM python:3.11.11-alpine3.21 AS builder
ARG ANDROIDTVBACKGROUND_REPO=https://github.com/adelatour11/androidtvbackground.git
ARG Roboto_Light_URL=https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf
ARG SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.33/supercronic-linux-amd64
WORKDIR /app

# Install androidtvbackground app and deps
RUN apk update && \
    apk add -q git > /dev/null && \
    git clone -q $ANDROIDTVBACKGROUND_REPO . && \
    rm -rf .git README.md && \
    pip -qq install --no-cache-dir -r /app/requirements.txt && \
    python -m pip uninstall --root-user-action=ignore -y setuptools wheel pip

# Add font
ADD $Roboto_Light_URL Roboto-Light.ttf
# Use supercronic instead of cron for better container support
ADD $SUPERCRONIC_URL supercronic

# Create main image   
FROM alpine:3.21
ARG VERSION
ARG SUPERCRONIC_SHA1SUM=71b0d58cc53f6bd72cf2f293e09e294b79c666d8
LABEL org.opencontainers.image.source="https://github.com/adelatour11/androidtvbackground" \
      org.opencontainers.image.description="Create background wallpapers from Plex/TMDB/Trakt" \
      org.opencontainers.image.authors="adelatour11" \
      org.opencontainers.image.version=$VERSION

# Set volume and copy files
VOLUME /config
VOLUME /backgrounds
COPY --from=builder /app /app
COPY --from=builder /usr/local/bin/python /usr/local/bin/python
COPY --from=builder /usr/local/lib/ /usr/local/lib/
COPY . .

# Setup env & update perms
RUN mv /app/supercronic /supercronic && \
    echo "$SUPERCRONIC_SHA1SUM  supercronic" | sha1sum -c - && \
    chmod -R ug=rw,o=rw,a-x+X /app create_post_scripts.sh entrypoint.sh run.sh supercronic && \
    chmod +x create_post_scripts.sh entrypoint.sh supercronic

# Run as nonroot
USER 99:100
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/supercronic", "-quiet", "/app/cron"]
