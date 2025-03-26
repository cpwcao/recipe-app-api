#from a images file
FROM python:3.9-alpine3.13
LABEL maintainer="cpwcao <peiwei.cao@gmail.com>"

ENV PYTHONUNBUFFERED="1"

COPY ./app/requirements.txt /tmp/requirements.txt
COPY ./app/requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    chmod +777 /app/wait-for-db.sh && \
    apk add --update  postgresql-client && \
    apk add --update  --virtual .tmp-build-deps \
    # apk add --update --no-cache postgresql-client && \
    # apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "True" ]; then \
       /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser \
        --disabled-password \
        --no-create-home \
        django_user
    
ENV PATH="/py/bin:$PATH"

USER django_user

# Command to install dependencies when needed
CMD ["/bin/sh", "-c", "pip install -r /tmp/requirements.txt && gunicorn app.wsgi:application --bind 0.0.0.0:8000"]