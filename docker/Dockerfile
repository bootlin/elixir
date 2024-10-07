FROM debian:bookworm AS build

RUN \
  apt-get update && \
  apt-get --no-install-recommends -y install \
    python3 \
    python3-pip \
    python3-dev \
    libdb-dev \
    build-essential

WORKDIR /build/

# TODO switch to berkeleydb
# NOTE wheel version MUST be sycnhronized with requirements.txt
RUN pip wheel bsddb3==6.2.9

FROM debian:bookworm

RUN \
  apt-get update && \
  apt-get --no-install-recommends -y install \
    python3 \
    python3-pip \
    python3-venv \
    universal-ctags \
    libdb5.3 \
    perl \
    git \
    apache2 \
    libapache2-mod-wsgi-py3 \
    libjansson4 \
    libyaml-0-2 \
    wget

COPY . /usr/local/elixir/

WORKDIR /usr/local/elixir/

COPY --from=build /build/bsddb3-6.2.9-*.whl /tmp/build/

RUN python3 -m venv venv && \
    . ./venv/bin/activate && \
    pip install /tmp/build/bsddb3-6.2.9-*.whl && \
    pip install -r requirements.txt

RUN mkdir -p /srv/elixir-data/

COPY ./docker/000-default.conf /etc/apache2/sites-available/000-default.conf

RUN a2enmod rewrite

EXPOSE 80

ARG ELIXIR_VERSION
ENV ELIXIR_VERSION=$ELIXIR_VERSION

ENTRYPOINT ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
