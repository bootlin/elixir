FROM debian:bookworm

RUN \
  apt-get update && \
  apt-get --no-install-recommends -y install \
    python3 \
    python3-pip \
    python3-falcon \
    python3-jinja2 \
    python3-bsddb3 \
    python3-pytest \
    python3-pygments \
    perl \
    git \
    apache2 \
    libapache2-mod-wsgi-py3 \
    libjansson4 \
    libyaml-0-2 \
    wget

RUN \
  wget https://bootlin.com/pub/elixir/universal-ctags_0+git20200526-0ubuntu1_amd64.deb

RUN \
  dpkg -i universal-ctags_0+git20200526-0ubuntu1_amd64.deb

COPY . /usr/local/elixir/

RUN mkdir -p /srv/elixir-data/

# apache elixir config, see elixir README
# make apache less stricter about cgitb spam headers
COPY ./docker/000-default.conf /etc/apache2/sites-available/000-default.conf

RUN \
  echo -e "\nHttpProtocolOptions Unsafe" >> /etc/apache2/apache.conf && \
  a2enmod cgi rewrite

EXPOSE 80

ENTRYPOINT ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
