#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Backfill missing profiles (safe to run every deploy)
python manage.py shell -c "
from django.contrib.auth.models import User
from chat.models import Profile
for u in User.objects.all():
    Profile.objects.get_or_create(user=u)
" || true