# The Elixir Cross Referencer


Elixir is a source code cross-referencer inspired by
[LXR](https://en.wikipedia.org/wiki/LXR_Cross_Referencer). It's written
in Python and its main purpose is to index every release of a C or C++
project (like the Linux kernel) while keeping a minimal footprint.

It uses Git as a source-code file store and Berkeley DB for cross-reference
data. Internally, it indexes Git *blobs* rather than trees of files to avoid
duplicating work and data. It has a straightforward data structure
(reminiscent of older LXR releases) to keep queries simple and fast.

You can see it in action on https://elixir.bootlin.com/

# Requirements

* Python >= 3.5
* The Jinja2 and Pygments (>= 2.2) Python libraries
* Berkeley DB (and its Python binding)
* Exuberant Ctags
* Perl (for non-greedy regexes)
* Falcon and mod_wsgi (for the REST api)

# Installation

## Architecture

Elixir has the following architecture:

    .---------------.----------------.
    | CGI interface | REST interface |
    |---------------|----------------.
    | Query command | Update command |
    |---------------|----------------|
    |          Shell script          |
    '--------------------------------'

The shell script (`script.sh`) is the lower layer and provides commands
to interact with Git and other Unix utilities. The Python commands use
the shell script's services to provide access to the annotated source
code and identifier lists (`query.py`) or to create and update the
databases (`update.py`). Finally, the CGI interface (`web.py`) and
the REST interface (`api.py`) use the query interface to generate HTML
pages and to answer REST queries, respectively.


When installing the system, you should test each layer manually and make
sure it works correctly before moving on to the next one.

## Install Manually

### Install Dependences

> For RedHat/CentOS

```
yum install python36-jinja2 python36-pygments python36-bsddb3 python3-falcon global-ctags git httpd
```
> For Debian

```
sudo apt install python3 python3-jinja2 python3-pygments python3-bsddb3 python3-falcon exuberant-ctags perl git apache2 libapache2-mod-wsgi-py3
```

To enable the REST api, follow the installation instructions on [mod_wsgi](https://github.com/GrahamDumpleton/mod_wsgi)
and connect it to the apache installation as detailed in https://github.com/GrahamDumpleton/mod_wsgi#connecting-into-apache-installation

To know which packages to install, you can also read the Docker files in the `docker/` directory
to know what packages Elixir needs in your favorite distribution.

### Download Elixir Project

```
git clone https://github.com/bootlin/elixir.git /usr/local/elixir/
```

### Create Directory

```
mkdir -p /path/elixir-data/linux/repo
mkdir -p /path/elixir-data/linux/data
```

### Set environment variables

Two environment variables are used to tell Elixir where to find the project's
local git repository and its databases:

* LXR_REPO_DIR (the git repository directory for your project)
* LXR_DATA_DIR (the database directory for your project)

Now open `/etc/profile` and append the following content.

```
export LXR_REPO_DIR=/path/elixir-data/linux/repo
export LXR_DATA_DIR=/path/elixir-data/linux/data
```
And then run `source /etc/profile`.

### Clone Kernel source code

```
git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git /path/elixir-data/linux/repo/
```

### First Test

```
cd /usr/local/elixir/
./script.sh list-tags
```

### Create Database

```
./update.py
```

> Generating the full database can take a long time: it takes about 15 hours on a Xeon E3-1245 v5 to index 1800 tags in the Linux kernel. For that reason, you may want to tweak the script (for example, by limiting the number of tags with a "head") in order to test the update and query commands. You can even create a new Git repository and just create one tag instead of using the official kernel repository which is very large.

### Second Test

Verify that the queries work:

```
$ ./query.py file v4.10 /kernel/sched/clock.c
$ ./query.py ident v4.10 raw_spin_unlock_irq
```

Note: `v4.10` can be replaced with any other tag.

### Configure httpd

The CGI interface (`web.py`) is meant to be called from your web
server. Since it includes support for indexing multiple projects,
it expects a different variable (`LXR_PROJ_DIR`) which points to a
directory with a specific structure:

* <LXR_PROJ_DIR>
  * <project 1>
    * data
    * repo
  * <project 2>
    * data
    * repo
  * <project 3>
    * data
    * repo

It will then generate the other two variables upon calling the query
command.

Now open `/etc/httpd/conf.d/elixir.conf` and write the following content.
Note: If using apache2 (Ubuntu/Debian) instead of httpd (RedHat/Centos),
the default config file to edit is: `/etc/apache2/sites-enabled/000-default.conf`

```
HttpProtocolOptions Unsafe
# Required for HTTP
<Directory /usr/local/elixir/http/>
    Options +ExecCGI
    AllowOverride None
    Require all granted
    SetEnv PYTHONIOENCODING utf-8
    SetEnv LXR_PROJ_DIR /path/elixir-data
</Directory>

# Required for the REST API
<Directory /usr/local/elixir/api/>
    SetHandler wsgi-script
    Require all granted
    SetEnv PYTHONIOENCODING utf-8
    SetEnv LXR_PROJ_DIR /path/elixir-data
</Directory>

AddHandler cgi-script .py
#Listen 80
<VirtualHost *:80>
    ServerName xxx
    DocumentRoot /usr/local/elixir/http

    # To enable REST api after installing mod_wsgi: Fill path and uncomment:
    #WSGIScriptAlias /api /usr/local/elixir/api/api.py

    RewriteEngine on
    RewriteRule "^/$" "/linux/latest/source" [R]
    RewriteRule "^/(?!api).*/(source|ident|search)" "/web.py" [PT]
</VirtualHost>
```

cgi and rewrite support has been enabled by default in RHEL/CentOS, but you should enable it manually if your distribution is Debian/Ubuntu.

```
a2enmod cgi rewrite
```

Finally, start the httpd server.

```
systemctl start httpd
```

### Using a cache to improve performance

At Bootlin, we're using the [Varnish http cache](https://varnish-cache.org/)
as a front-end to reduce the load on the server running the Elixir code.

    .-------------.           .---------------.           .-----------------------.
    | Http client | --------> | Varnish cache | --------> | Apache running Elixir |
    '-------------'           '---------------'           '-----------------------'

### Keeping Elixir databases up to date

To keep your Elixir databases up to date and index new versions that are released,
we're proposing to use a script like `utils/update-elixir-data` which is called
through a daily cron job.

### Keeping git repository disk usage under control

As you keep updating your git repositories, you may notice that some can become
considerably bigger than they originally were. This seems to happen when a `gc.log`
file appears in a big repository, apparently causing git's garbage collector (`git gc`)
to fail, and therefore causing the repository to consume disk space at a fast
pace every time new objects are fetched.

When this happens, you can save disk space by packing git directories as follows:
```
cd <bare-repo>
git prune
rm gc.log
git gc --aggressive
```

Actually, a second pass with the above commands will save even more space.

To process multiple git repositories in a loop, you may use the
`utils/pack-repositories` that we are providing, run from the directory
where all repositories are found.

## Building Docker images

Docker files are provided in the `docker/` directory. To generate your own
Docker image for indexing the sources of a project (for example for the Musl
project which is much faster to index that Linux), download the `Dockerfile`
file for your target distribution and run:

    $ docker build -t elixir --build-arg GIT_REPO_URL=git://git.musl-libc.org/musl --build-arg PROJECT=musl .

Then you can use your new container as follows (you get the container id from the output of `docker build`):

    $ docker run <container-id>

You can the open the below URL in a browser on your host: http://172.17.0.2/musl/latest/source
(change the container IP address if you don't get the default one)

# Database design

`./update.py` stores a bidirectionnal mapping between git object hashes ("blobs") and a sequential key.
The goal of indexing such hashes is to reduce their storage footprint (20 bytes for a SHA-1 hash
versus 4 bytes for a 32 bit integer).

A detailed diagram of the databases will be provided. Until then, just use the Source, Luke.

# Hardware requirements

Performance requirements depend mostly on the amount of traffic that you get
on your Elixir service. However, a fast server also helps for the initial
indexing of the projects.

SSD storage is strongly recommended because of the frequent access to
git repositories.

At Bootlin, here are a few details about the server we're using:

* As of July 2019, our Elixir service consumes 17 GB of data (supporting all projects),
  or for the Linux kernel alone (version 5.2 being the latest), 12 GB for indexing data,
  and 2 GB for the git repository.
* We're using an LXD instance with 8 GB of RAM on a cloud server with 8 CPU cores
  running at 3.1 GHz.

# Supporting a new project

Elixir has a very simple modular architecture that allows to support
new source code projects by just adding a new file to the Elixir sources.

Elixir's assumptions:

* Project sources have to be available in a git repository
* All project releases are associated to a given git tag. Elixir
  only considers such tags.

First make an installation of Elixir by following the above instructions.
See the `projects` subdirectory for projects that are already supported.

Once Elixir works for at least one project, it's time to clone the git
repository for the project you want to support:

    cd /srv/git
    git clone --bare https://github.com/zephyrproject-rtos/zephyr

Now, in your `LXR_PROJ_DIR` directory, create a new directory for the
new project:

    cd $LXR_PROJ_DIR
    mkdir -p zephyr/data
    ln -s /srv/git/zephyr.git repo
    export LXR_DATA_DIR=$LXR_PROJ_DIR/data
    export LXR_REPO_DIR=$LXR_PROJ_DIR/repo

Now, go back to the Elixir sources and test that tags are correctly
extracted:

    ./script.sh list-tags

Depending on how you want to show the available versions on the Elixir pages,
you may have to apply substitutions to each tag string, for example to add
a `v` prefix if missing, for consistency with how other project versions are
shown. You may also decide to ignore specific tags. All this can be done
by redefining the default `list_tags()` function in a new `project/<projectname>.sh`
file. Here's an example (`projects/zephyr.sh` file):

    list_tags()
    {
        echo "$tags" |
        grep -v '^zephyr-v'
    }

Note that `<project_name>` **must** match the name of the directory that
you created under `LXR_PROJ_DIR`.

The next step is to make sure that versions are classified as you wish
in the version menu. This classification work is done through the
`list_tags_h()` function which generates the output of the `./scripts.sh list-tags -h`
command. Here's what you get for the Linux project:

    v4 v4.16 v4.16
    v4 v4.16 v4.16-rc7
    v4 v4.16 v4.16-rc6
    v4 v4.16 v4.16-rc5
    v4 v4.16 v4.16-rc4
    v4 v4.16 v4.16-rc3
    v4 v4.16 v4.16-rc2
    v4 v4.16 v4.16-rc1
    ...

The first column is the top level menu entry for versions.
The second one is the next level menu entry, and
the third one is the actual version that can be selected by the menu.
Note that this third entry must correspond to the exact
name of the tag in git.

If the default behavior is not what you want, you will have
to customize the `list_tags_h` function.

You should also make sure that Elixir properly identifies
the most recent versions:

    ./script.sh get-latest

If needed, customize the `get_latest()` function.

You are now ready to generate Elixir's database for your
new project:

    ./update.py

You can then check that Elixir works through your http server.

# REST api usage
After configuring httpd, you can test the api usage:

## ident query

Send a get request to ```/api/ident/<Project>/<Ident>?version=<version>```.
For example:

    curl http://127.0.0.1/api/ident/barebox/cdev?version=latest

The response body is of the following structure:
```
{
    "definitions":
        [{"path": "commands/loadb.c", "line": 71, "type": "variable"}, ...],
    "references": 
        [{"path": "arch/arm/boards/cm-fx6/board.c", "line": "64,64,71,72,75", "type": null}, ...]
}
```

Note: this documentation applies to version 1.0 of Elixir.
