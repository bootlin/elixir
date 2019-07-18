The Elixir Cross Referencer
===========================

Elixir is a source code cross-referencer inspired by
[LXR](https://en.wikipedia.org/wiki/LXR_Cross_Referencer). It's written
in Python and its main purpose is to index every release of a C or C++
project (like the Linux kernel) while keeping a minimal footprint.

It uses Git as a source-code file store and Berkeley DB for cross-reference
data. Internally, it indexes Git *blobs* rather than trees of files to avoid
duplicating work and data. It has a straightforward data structure
(reminiscent of older LXR releases) to keep queries simple and fast.

You can see it in action on https://elixir.bootlin.com/

Requirements
------------

* Python >= 3.5
* The Jinja2 and Pygments Python libraries
* Berkeley DB (and its Python binding)
* Exuberant Ctags
* Perl (for non-greedy regexes)

Installation
------------

See the next paragraph for building ready-made Docker images.

Elixir has the following architecture:

    .---------------.
    | CGI interface |
    |---------------|----------------.
    | Query command | Update command |
    |---------------|----------------|
    |          Shell script          |
    '--------------------------------'

The shell script ("script.sh") is the lower layer and provides commands
to interact with Git and other Unix utilities. The Python commands use
the shell script's services to provide access to the annotated source
code and identifier lists ("query.py") or to create and update the
databases ("update.py"). Finally, the CGI interface ("web.py") uses the
query interface to generate HTML pages.

When installing the system, you should test each layer manually and make
sure it works correctly before moving on to the next one.

Two environment variables are used to tell Elixir where to find its
local Git repository and its database directory:

* LXR_REPO_DIR (the directory that contains your Git project)
* LXR_DATA_DIR (the directory that will contain your databases)

When both are set up, you should be able to test that the script
works:

    $ ./script.sh list-tags

then generate the databases:

    $ ./update.py

and verify that the queries work:

    $ ./query.py file v4.10 /kernel/sched/clock.c
    $ ./query.py ident v4.10 raw_spin_unlock_irq

Generating the full database can take a long time: it takes about
15 hours on a Xeon E3-1245 v5 to index 1800 tags in the Linux kernel.
For that reason, you may want to tweak the script (for example, by
limiting the number of tags with a "head") in order to test the
update and query commands.

The CGI interface ("web.py") is meant to be called from your web
server. Since it includes support for indexing multiple projects,
it expects a different variable ("LXR_PROJ_DIR") which points to a
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

Here is an example configuration for Apache:

    <Directory /usr/local/elixir/http/>
        Options +ExecCGI
        AllowOverride None
        Require all granted
        SetEnv PYTHONIOENCODING utf-8
        SetEnv LXR_PROJ_DIR /srv/elixir-data
    </Directory>

    AddHandler cgi-script .py

    <VirtualHost *:80>
        ServerName elixir.example.com
        DocumentRoot /usr/local/elixir/http

        RewriteEngine on
        RewriteRule "^/$" "/linux/latest/source" [R]
        RewriteRule "^/.*/(source|ident|search)" "/web.py" [PT]
    </VirtualHost>

Don't forget to enable cgi and rewrite support with `a2enmod cgi rewrite`.

Building Docker images
----------------------

Docker files are provided in the "docker/" directory. To generate your own
Docker image for indexing the Linux kernel sources (for example),
download the "Dockerfile" file for your target distribution and run:

    $ docker build -t elixir --build-arg GIT_REPO_URL=git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git .

Hardware requirements
---------------------

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

Supporting a new project
------------------------

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

Note: this documentation applies to version 0.3 of Elixir.
