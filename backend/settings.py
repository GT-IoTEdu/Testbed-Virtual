import os
from urllib.parse import urlparse

# Database configuration from environment variables
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DB', 'iot_edu'),
        'USER': os.getenv('MYSQL_USER', 'IoT_EDU'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', 'sua_senha_mysql_aqui'),
        'HOST': os.getenv('MYSQL_HOST', 'mysql'),
        'PORT': os.getenv('MYSQL_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Alternative: Use DATABASE_URL if preferred
if 'DATABASE_URL' in os.environ:
    db_url = urlparse(os.environ['DATABASE_URL'])
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': db_url.path[1:],
        'USER': db_url.username,
        'PASSWORD': db_url.password,
        'HOST': db_url.hostname,
        'PORT': db_url.port,
    }
