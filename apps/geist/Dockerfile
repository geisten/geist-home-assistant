FROM ghcr.io/home-assistant/base:3.22

ARG BUILD_ARCH
ARG BUILD_VERSION=0.1.0

RUN apk add --no-cache socat

COPY rootfs /
# Materialized and verified by scripts/verify-runtime-lock.sh before the
# build; the build itself performs no network access for the runtime.
COPY build/${BUILD_ARCH}/geist /usr/bin/geist
RUN chmod 0755 /run.sh /healthcheck.sh /preflight.sh /usr/bin/geist
ENV GEIST_BUILD_ARCH=${BUILD_ARCH}

LABEL \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.type="app" \
    io.hass.arch="${BUILD_ARCH}"

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD ["/healthcheck.sh"]
CMD ["/run.sh"]
