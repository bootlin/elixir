The Elixir Cross Referencer
===========================

Elixir is a source code cross-referencer inspired by
[LXR](https://en.wikipedia.org/wiki/LXR_Cross_Referencer). It's written
in Python and its main purpose is to index every release of the Linux
kernel while keeping a minimal footprint.

It uses Git as a source-code file store and Berkeley DB for cross-reference
data. Internally, it indexes Git *blobs* rather than trees of files to avoid
duplicating work and data. It has a straightforward data structure
(reminiscent of older LXR releases) to keep queries simple and fast.


Requirements
------------

* Python 3
* The Jinja2 and Pygments Python libraries
* Berkeley DB (and its Python binding)
* Exuberant Ctags
* Perl (for non-greedy regexes)


Installation
------------

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
command. For now, three projects are hard-coded into the shell script
(to handle version grouping and display): Linux, U-Boot and Busybox.

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

Note: this documentation applies to version 0.2 of Elixir.
