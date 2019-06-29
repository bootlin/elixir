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

RUN \
    : "${GIT_REPO_URL:?set GIT_REPO_URL to the repo git url}"

RUN \
    echo "repo url to index: ${GIT_REPO_URL}"

RUN \
  yum install -y \
    python36-jinja2 \
    python36-pygments \
    python36-bsddb3 \
    global-ctags \
    git
    # httpd & perl is inherited from upstream openshift image


RUN \
  git clone https://github.com/bootlin/elixir.git /usr/local/elixir/

RUN \
  mkdir -p /srv/elixir-data/linux/repo && \
  mkdir -p /srv/elixir-data/linux/data && \
  git clone "${GIT_REPO_URL}" /srv/elixir-data/linux/repo/

ENV LXR_REPO_DIR /srv/elixir-data/linux/repo
ENV LXR_DATA_DIR /srv/elixir-data/linux/data

RUN \
  cd /usr/local/elixir/ && \
  ./script.sh list-tags && \
  ./update.py

# apache elixir config, see elixir README
# NB: Change /linux/ to the name of the project you want as default shown
# apache HttpProtolOptions workaround
RUN \
  echo $'<Directory /usr/local/elixir/http/>\n\
    Options +ExecCGI\n\
    AllowOverride None\n\
    Require all granted\n\
    SetEnv PYTHONIOENCODING utf-8\n\
    SetEnv LXR_PROJ_DIR /srv/elixir-data\n\
</Directory>\n\
AddHandler cgi-script .py\n\
<VirtualHost *:8080>\n\
    ServerName MY_LOCAL_IP\n\
    DocumentRoot /usr/local/elixir/http\n\
    RewriteEngine on\n\
    RewriteRule "^/$" "/linux/latest/source" [R]\n\
    RewriteRule "^/.*/(source|ident|search)" "/web.py" [PT]\n\
</VirtualHost>' > /etc/httpd/conf.d/000-elixir.conf \
&& echo -e "\nHttpProtocolOptions Unsafe" >> /etc/httpd/conf/httpd.conf
  # a2enmod cgi rewrite - enabled by default in RHEL/centos


# Make sure the final image runs as unprivileged user
USER 1001

ENTRYPOINT ["/usr/bin/run-httpd"]
