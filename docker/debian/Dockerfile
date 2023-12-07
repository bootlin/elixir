FROM debian:bookworm
ARG GIT_REPO_URL
ARG PROJECT

RUN \
    : "${GIT_REPO_URL:?set GIT_REPO_URL to the repo git url}"

RUN \
    : "${PROJECT:?set PROJECT to set the project name}"

RUN \
    echo "repo url to index: ${GIT_REPO_URL}"


RUN \
  apt-get update && \
  apt-get -y install \
    python3 \
    python3-pip \
    python3-falcon \
    python3-jinja2 \
    python3-bsddb3 \
    python3-pytest \
    pipx \
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

RUN \
  wget https://bootlin.com/pub/elixir/Pygments-2.6.1.elixir-py3-none-any.whl

RUN \
  pipx install ./Pygments-2.6.1.elixir-py3-none-any.whl

RUN \
  git config --global user.email 'elixir@dummy.com' && \
  git config --global user.name 'elixir'

RUN \
  git clone https://github.com/bootlin/elixir.git /usr/local/elixir/

RUN \
  mkdir -p /srv/elixir-data/ && \
  mkdir -p /srv/elixir-data/$PROJECT/repo && \
  mkdir -p /srv/elixir-data/$PROJECT/data && \
  git clone --bare "${GIT_REPO_URL}" /srv/elixir-data/$PROJECT/repo/ && \
  git config --global --add safe.directory /srv/elixir-data/$PROJECT/repo

ENV LXR_REPO_DIR /srv/elixir-data/$PROJECT/repo
ENV LXR_DATA_DIR /srv/elixir-data/$PROJECT/data

RUN \
  cd /usr/local/elixir/ && \
  ./script.sh list-tags && \
  python3 -u ./update.py && \
  chown -R www-data:www-data /srv/elixir-data/$PROJECT/repo

# apache elixir config, see elixir README
# make apache less stricter about cgitb spam headers
COPY ./docker/debian/000-default.conf /etc/apache2/sites-available/000-default.conf

RUN \
  echo -e "\nHttpProtocolOptions Unsafe" >> /etc/apache2/apache.conf && \
  a2enmod cgi rewrite

EXPOSE 80

ENTRYPOINT ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
