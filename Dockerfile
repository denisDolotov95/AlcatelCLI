FROM python:3.10.16-slim

ENV LANG='ru_RU.UTF-8' \
    LANGUAGE='ru_RU.UTF-8' \
    LC_ALL='ru_RU.UTF-8'

RUN apt-get update && \
    apt-get -y install locales && \
    locale-gen ru_RU.UTF-8 && \
    echo "ru_RU.UTF-8 UTF-8" >> /etc/locale.gen && \
    apt-get -y install tzdata && \
    ln -fs /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# Set timezone Europe/Moscow
RUN 

WORKDIR /usr/src
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "app"]