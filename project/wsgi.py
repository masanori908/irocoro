"""
WSGI config for project project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# 起動時にマイグレーションを自動実行（Render対応）
from django.core.management import call_command
try:
    call_command('migrate', '--noinput')
except Exception:
    pass

application = get_wsgi_application()
