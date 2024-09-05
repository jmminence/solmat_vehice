import sys, os

INTERP = os.path.join(os.environ['HOME'], 'web', 'env', 'bin', 'python3.6')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

cwd = os.getcwd()
sys.path.append("/home/vehice/web/src")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vehice.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
