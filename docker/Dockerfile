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

# NOTE wheel version MUST be sycnhronized with requirements.txt
RUN pip wheel berkeleydb==18.1.10

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

COPY ./requirements.txt /usr/local/elixir/requirements.txt

WORKDIR /usr/local/elixir/

COPY --from=build /build/berkeleydb-*.whl /tmp/build/

RUN python3 -m venv venv && \
    . ./venv/bin/activate && \
    pip install /tmp/build/berkeleydb-*.whl && \
    pip install -r requirements.txt

COPY . /usr/local/elixir/

RUN mkdir -p /srv/elixir-data/

COPY ./docker/000-default.conf /etc/apache2/sites-available/000-default.conf

RUN a2enmod rewrite

EXPOSE 80

ARG ELIXIR_VERSION
ENV ELIXIR_VERSION=$ELIXIR_VERSION

ENV ELIXIR_ROOT=/srv/elixir-data
ENV PATH="/usr/local/elixir/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/elixir/utils:$PATH"

ENTRYPOINT ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
