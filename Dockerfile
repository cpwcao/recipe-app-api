FROM python:3.9-alpine3.13
LABEL maintainer="cpwcao <peiwei.cao@gmail.com>" 

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PATH="/py/bin:$PATH" \
    DEV="True"

# Force update Alpine package index & keyring
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \
    apk add --no-cache \
        build-base linux-headers pcre-dev && \
    apk update && \
    apk upgrade --available && \
    apk add --no-cache \
        alpine-keys \
        postgresql-client \
        jpeg-dev && \
    apk add --no-cache jpeg-dev zlib-dev && \
    apk add --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev zlib zlib-dev && \
    apk del .tmp-build-deps && \
    rm -rf /var/cache/apk/*
    

# Install Python dependencies
RUN python -m venv /py && \
    /py/bin/pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    /py/bin/pip install --upgrade pip 
# Copy requirements
COPY ./app/requirements.txt /tmp/requirements.txt
COPY ./app/requirements.dev.txt /tmp/requirements.dev.txt

# Install dependencies
RUN /py/bin/pip install --no-cache-dir -r /tmp/requirements.txt && \ 
    if [ "$DEV" = "True" ]; then \
    /py/bin/pip install --no-cache-dir -r /tmp/requirements.dev.txt; \
    fi && \
    /py/bin/pip install --no-cache-dir uwsgi 

WORKDIR /app
COPY ./app /app

# Create non-root user
RUN adduser --disabled-password --no-create-home django_user && \
    mkdir -p /vol/web/media /vol/web/static && \
    chown -R django_user:django_user /vol && \
    chmod -R 755 /vol

USER django_user

EXPOSE 8000 

CMD ["/py/bin/uwsgi", "--http", ":8000", "--module", "app.wsgi:application", "--workers=2", "--max-requests=500"]
