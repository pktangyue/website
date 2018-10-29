from .settings import *

DEBUG = False

PARENT_HOST = os.environ.get('DOMAIN', '')
HOST_PORT = ''

STATIC_URL = '//assets.' + PARENT_HOST + '/'

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'sassc {infile} {outfile}'),
)

DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.postgresql',
        'NAME'    : os.environ.get('POSTGRES_DB', ''),
        'USER'    : os.environ.get('POSTGRES_USER', ''),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
        'HOST'    : 'postgres',
        'PORT'    : '5432',
    }
}
