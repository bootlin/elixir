# Openshift Dockerfile for Centos7 Elixir Cross Referencer
# This will build a httpd 2.4.34+ service container running Elixir
# You may run this image on its own or as a component of a pod.
# Usage:
# Building: Docker Build dockerfile_path/ --build-arg GIT_REPO_URL=https://your-git-source-repo.git -t elixir
# Running: Docker run -p 8080:8080 elixir

FROM centos/httpd-24-centos7

LABEL author="David.Southwick@cern.ch"

# temporarily switch to root user
USER root

ARG GIT_REPO_URL
ARG PROJECT

RUN \
    : "${GIT_REPO_URL:?set GIT_REPO_URL to the repo git url}"

RUN \
    : "${PROJECT:?set PROJECT to set the project name}"

RUN \
    echo "repo url to index: ${GIT_REPO_URL}"

RUN \
  yum install -y \
    python36-jinja2 \
    python36-bsddb3 \
    python36-pip \
    python36-falcon \
    python36-pytest \
    rh-python36-mod_wsgi \
    perl-autodie \
    jansson \
    libyaml \
    git \
    wget
    # httpd & perl is inherited from upstream openshift image

RUN \
  wget https://bootlin.com/pub/elixir/universal-ctags-0+git~20e934e3-1.6.x86_64.rpm

RUN \
  rpm -iv universal-ctags-0+git~20e934e3-1.6.x86_64.rpm

RUN \
  wget https://bootlin.com/pub/elixir/Pygments-2.6.1.elixir-py3-none-any.whl

RUN \
  pip3 install Pygments-2.6.1.elixir-py3-none-any.whl

RUN \
  git clone https://github.com/bootlin/elixir.git /usr/local/elixir/

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
# apache HttpProtolOptions workaround
RUN \
  echo PERpcmVjdG9yeSAvdXNyL2xvY2FsL2VsaXhpci9odHRwLz4KICAgIE9wdGlvbnMgK0V4ZWNDR0kKICAgIEFsbG93T3ZlcnJpZGUgTm9uZQogICAgUmVxdWlyZSBhbGwgZ3JhbnRlZAogICAgU2V0RW52IFBZVEhPTklPRU5DT0RJTkcgdXRmLTgKICAgIFNldEVudiBMWFJfUFJPSl9ESVIgL3Nydi9lbGl4aXItZGF0YQo8L0RpcmVjdG9yeT4KPERpcmVjdG9yeSAvdXNyL2xvY2FsL2VsaXhpci9hcGkvPgogICAgU2V0SGFuZGxlciB3c2dpLXNjcmlwdAogICAgUmVxdWlyZSBhbGwgZ3JhbnRlZAogICAgU2V0RW52IFBZVEhPTklPRU5DT0RJTkcgdXRmLTgKICAgIFNldEVudiBMWFJfUFJPSl9ESVIgL3Nydi9lbGl4aXItZGF0YQo8L0RpcmVjdG9yeT4KQWRkSGFuZGxlciBjZ2ktc2NyaXB0IC5weQo8VmlydHVhbEhvc3QgKjo4MDgwPgogICAgU2VydmVyTmFtZSBNWV9MT0NBTF9JUAogICAgRG9jdW1lbnRSb290IC91c3IvbG9jYWwvZWxpeGlyL2h0dHAKICAgIFdTR0lTY3JpcHRBbGlhcyAvYXBpIC91c3IvbG9jYWwvZWxpeGlyL2FwaS9hcGkucHkKICAgIEFsbG93RW5jb2RlZFNsYXNoZXMgT24KICAgIFJld3JpdGVFbmdpbmUgb24KICAgIFJld3JpdGVSdWxlICJeLyQiICIvbGludXgvbGF0ZXN0L3NvdXJjZSIgW1JdCiAgICBSZXdyaXRlUnVsZSAiXi8oPyFhcGl8YWNwKS4qLyhzb3VyY2V8aWRlbnR8c2VhcmNoKSIgIi93ZWIucHkiIFtQVF0KICAgIFJld3JpdGVSdWxlICJeL2FjcCIgIi9hdXRvY29tcGxldGUucHkiIFtQVF0KPC9WaXJ0dWFsSG9zdD4= | base64 -d > /etc/httpd/conf.d/000-elixir.conf \
&& echo -e "\nHttpProtocolOptions Unsafe" >> /etc/httpd/conf/httpd.conf
  # a2enmod cgi rewrite - enabled by default in RHEL/centos


# Make sure the final image runs as unprivileged user
USER 1001

ENTRYPOINT ["/usr/bin/run-httpd"]
