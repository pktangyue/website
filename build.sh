#!/usr/bin/env bash
python3 manage.py migrate && \
python3 manage.py note_build /QuiverWeb/Quiver.qvlibrary && \
python3 manage.py collectstatic --noinput -i '*.scss' && \
python3 manage.py blog_build
