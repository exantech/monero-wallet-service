#!/bin/bash

BRANCH=${1:-master}
mkdir -p debian/var/www/env/monero-wallet-service/app >/dev/null 2>&1
rm -rf debian/var/www/env/monero-wallet-service/*

VERSION=$(git describe --always --tags | sed -re "s/-/~${BRANCH}+/" | sed -re 's/^[^0-9]//g')

rm -rf build
mkdir build

virtualenv -p python3.6 build/env
build/env/bin/pip install --trusted-host ci2-pypi.ghcg.com --extra-index-url http://ci2-pypi.ghcg.com/ ..

fpm -s dir -t deb \
    -n exantech-monero-wallet-service \
    -v ${VERSION} \
    -a all \
    -d python3.6 \
    -d libpython3.6 \
    -d libpq5 \
    --prefix=/ \
    --post-install=debian/postinst \
    ../run.py=/var/www/env/monero-wallet-service/run.py \
    ../pusher.py=/var/www/env/monero-wallet-service/pusher.py \
    ../migration.py=/var/www/env/monero-wallet-service/migration.py \
    ../settings.py=/var/www/env/monero-wallet-service/settings.py \
    ../service/=/var/www/env/monero-wallet-service/service/ \
    ../api/=/var/www/env/monero-wallet-service/api/ \
    ../swagger/=/var/www/env/monero-wallet-service/swagger/ \
    ./build/env/lib/=/var/www/env/monero-wallet-service/lib/ \
    ./build/env/bin/=/var/www/env/monero-wallet-service/bin/ \
    ./debian/etc/=/etc/ \
