# One image for every offline stage: Python plus SpamAssassin.
# Network is used only while building; every run uses `docker run --network none` (ENVIRONMENT.md).
# Base image pinned by digest, SpamAssassin by exact package version: a rebuild gets the same
# versions or fails loudly. Its Debian dependencies are not pinned (see ENVIRONMENT.md, Not verified).
FROM python@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

RUN apt-get update \
 && apt-get install -y --no-install-recommends spamassassin=4.0.1-1~deb12u1 \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Keep the mounted repo free of bytecode caches.
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /work
