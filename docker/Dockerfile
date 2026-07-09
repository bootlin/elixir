FROM debian:bookworm AS build

RUN \
  apt-get update && \
  apt-get --no-install-recommends -y install \
    git build-essential pkg-config autoconf automake \
    python3 python3-pip python3-dev python3-docutils \
    libdb-dev \
    libseccomp-dev libjansson-dev libyaml-dev libxml2-dev

WORKDIR /build-berkeleydb/

# NOTE wheel version MUST be sycnhronized with requirements.txt
RUN pip wheel berkeleydb==18.1.10

WORKDIR /build-ctags/

RUN git clone --branch v6.1.0 --depth 1 https://github.com/universal-ctags/ctags.git
WORKDIR ctags
RUN ./autogen.sh && ./configure && make -j $(nproc)

FROM debian:bookworm

RUN \
  apt-get update && \
  apt-get --no-install-recommends -y install \
    python3 \
    python3-pip \
    python3-venv \
    libdb5.3 \
    perl \
    git \
    apache2 \
    libapache2-mod-wsgi-py3 \
    libjansson4 \
    libyaml-0-2 \
    wget

COPY ./requirements.txt /usr/local/elixir/

WORKDIR /usr/local/elixir/

COPY --from=build /build-berkeleydb/berkeleydb-*.whl /tmp/build/

RUN python3 -m venv venv && \
    . ./venv/bin/activate && \
    pip install /tmp/build/berkeleydb-*.whl && \
    pip install -r requirements.txt

COPY --from=build /build-ctags/ctags/ctags /usr/bin/ctags

RUN mkdir -p /srv/elixir-data/

COPY ./docker/000-default.conf /etc/apache2/sites-available/000-default.conf
COPY ./docker/gitconfig /etc/gitconfig

RUN a2enmod rewrite headers

EXPOSE 80

ARG ELIXIR_VERSION

ENV ELIXIR_VERSION=$ELIXIR_VERSION \
    ELIXIR_ROOT=/srv/elixir-data \
    PATH="/usr/local/elixir/utils:/usr/local/elixir/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

COPY . /usr/local/elixir/

ENTRYPOINT ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
