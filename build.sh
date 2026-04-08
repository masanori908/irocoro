#!/usr/bin/env bash
# Render デプロイ時に実行されるビルドスクリプト
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
