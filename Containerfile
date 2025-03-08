FROM python:3.13.2-alpine3.21

ENV USER_NAME=yourarea
ENV GROUP_NAME=yourarea
ENV UID=1000
ENV GID=1000
ENV HOME_DIR=/home/${USER_NAME}
ENV APP_NAME="yourarea"
ENV APP_ROOT=/yourarea

RUN mkdir ${APP_ROOT}

WORKDIR ${APP_ROOT}

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

RUN pip3 install django pillow django-imagekit channels dotenv

RUN addgroup --gid "$GID" "$GROUP_NAME"

RUN adduser --uid 1000 -D -S -h ${HOME_DIR} -s /sbin/nologin -G ${GROUP_NAME} ${USER_NAME}

RUN chown -R ${USER_NAME}:${GROUP_NAME} /${APP_ROOT}

USER ${USER_NAME}
CMD python /yourarea/manage.py runserver 0.0.0.0:8000