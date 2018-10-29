FROM alpine:3.8
#RUN sed -i -- 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories
RUN apk add --update --no-cache uwsgi-python3 gcc python3-dev musl-dev sassc postgresql-dev
COPY requirements.txt /
#RUN pip3 install -r requirements.txt --index-url http://pypi.douban.com/simple --trusted-host pypi.douban.com
RUN pip3 install -r requirements.txt
ENV DJANGO_SETTINGS_MODULE=website.docker_settings
COPY . /code
WORKDIR /code
ENTRYPOINT /bin/sh build.sh && uwsgi --ini uwsgi_docker.ini
