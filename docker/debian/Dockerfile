FROM debian:latest
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
    python3-jinja2 \
    python3-pygments \
    python3-bsddb3 \
    python3-falcon \
    exuberant-ctags \
    perl \
    git \
    apache2 \
    libapache2-mod-wsgi-py3

RUN \
  git clone https://github.com/bootlin/elixir.git /usr/local/elixir/

RUN \
  mkdir -p /srv/elixir-data/

RUN \
  mkdir -p /srv/elixir-data/$PROJECT/repo && \
  mkdir -p /srv/elixir-data/$PROJECT/data && \
  git clone "${GIT_REPO_URL}" /srv/elixir-data/$PROJECT/repo/

ENV LXR_REPO_DIR /srv/elixir-data/$PROJECT/repo
ENV LXR_DATA_DIR /srv/elixir-data/$PROJECT/data

RUN \
  cd /usr/local/elixir/ && \
  ./script.sh list-tags && \
  ./update.py

# apache elixir config, see elixir README
# make apache less stricter about cgitb spam headers
RUN \
  echo PERpcmVjdG9yeSAvdXNyL2xvY2FsL2VsaXhpci9odHRwLz4KICAgIE9wdGlvbnMgK0V4ZWNDR0kKICAgIEFsbG93T3ZlcnJpZGUgTm9uZQogICAgUmVxdWlyZSBhbGwgZ3JhbnRlZAogICAgU2V0RW52IFBZVEhPTklPRU5DT0RJTkcgdXRmLTgKICAgIFNldEVudiBMWFJfUFJPSl9ESVIgL3Nydi9lbGl4aXItZGF0YQo8L0RpcmVjdG9yeT4KQWRkSGFuZGxlciBjZ2ktc2NyaXB0IC5weQo8VmlydHVhbEhvc3QgKjo4MD4KICAgIFNlcnZlck5hbWUgTVlfTE9DQUxfSVAKICAgIERvY3VtZW50Um9vdCAvdXNyL2xvY2FsL2VsaXhpci9odHRwCiAgICBSZXdyaXRlRW5naW5lIG9uCiAgICBSZXdyaXRlUnVsZSAiXi8kIiAiL2xpbnV4L2xhdGVzdC9zb3VyY2UiIFtSXQogICAgUmV3cml0ZVJ1bGUgIl4vLiovKHNvdXJjZXxpZGVudHxzZWFyY2gpIiAiL3dlYi5weSIgW1BUXQo8L1ZpcnR1YWxIb3N0Pgo= | base64 -d > /etc/apache2/sites-available/000-default.conf && \
  echo -e "\nHttpProtocolOptions Unsafe" >> /etc/apache2/apache.conf && \
  a2enmod cgi rewrite

EXPOSE 80

ENTRYPOINT ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
