FROM python:3.5.5

RUN apt-get update && apt-get install -y --no-install-recommends python3-virtualenv cmake

WORKDIR /usr/src/app/package

CMD ["bash", "-ex", "build_deb.sh", "master"]

