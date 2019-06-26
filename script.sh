#!/bin/sh

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2017  Mikaël Bouillot
#  <mikael.bouillot@bootlin.com>
#
#  Elixir is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Elixir is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Elixir.  If not, see <http://www.gnu.org/licenses/>.

if [ ! -d "$LXR_REPO_DIR" ]; then
    echo "$0: Can't find repository"
    exit 1
fi

version_dir()
{
    cat;
}

version_rev()
{
    cat;
}

get_tags()
{
    git tag |
    version_dir |
    sed 's/$/.0/' |
    sort -V |
    sed 's/\.0$//'
}

list_tags()
{
    echo "$tags"
}

list_tags_h()
{
    echo "$tags" |
    tac |
    sed -r 's/^(v[0-9]*)\.([0-9]*)(.*)$/\1 \1.\2 \1.\2\3/'
}

get_latest()
{
    git tag | version_dir | grep -v '\-rc' | sort -V | tail -n 1
}

get_type()
{
    v=`echo $opt1 | version_rev`
    git cat-file -t "$v:`denormalize $opt2`" 2>/dev/null
}

get_blob()
{
    git cat-file blob $opt1
}

get_file()
{
    v=`echo $opt1 | version_rev`
    git cat-file blob "$v:`denormalize $opt2`" 2>/dev/null
}

get_dir()
{
        v=`echo $opt1 | version_rev`
        git ls-tree -l "$v:`denormalize $opt2`" 2>/dev/null |
        awk '{print $2" "$5" "$4}' |
        grep -v ' \.' |
        sort -t ' ' -k 1,1r -k 2,2
}

tokenize_file()
{
    if [ "$opt1" = -b ]; then
        ref=$opt2
    else
        v=`echo $opt1 | version_rev`
        ref="$v:`denormalize $opt2`"
    fi
 
    git cat-file blob $ref 2>/dev/null |
    tr '\n' '\1' |
    perl -pe 's%((/\*.*?\*/|//.*?\001|"(\\.|.)*?"|# *include *<.*?>|\W)+)(\w+)?%\1\n\4\n%g' |
    head -n -1
}

list_blobs()
{
    v=`echo $opt2 | version_rev`

    if [ "$opt1" = '-p' ]; then
        format='\1 \2'
    elif [ "$opt1" = '-f' ]; then
        format='\1 \4'
    else
        format='\1'
        v=`echo $opt1 | version_rev`
    fi

    git ls-tree -r "$v" |
    sed -r "s/^\S* blob (\S*)\t(([^/]*\/)*(.*))$/$format/; /^\S* commit .*$/d"
}

untokenize()
{
    tr -d '\n' |
    sed 's/>/\*\//g' |
    sed 's/</\/\*/g' |
    tr '\1\2\3' '\n<>'
}

parse_defs()
{
    tmp=`mktemp -d`
    full_path=$tmp/$opt2
    git cat-file blob "$opt1" > "$full_path"
    ctags -x --c-kinds=+p-m "$full_path" |
    grep -av "^operator " |
    awk '{print $1" "$2" "$3}'
    rm "$full_path"
    rmdir $tmp
}

project=$(basename `dirname $LXR_REPO_DIR`)

plugin=projects/$project.sh
if [ -f "$plugin" ] ; then
    . $plugin
fi

cd "$LXR_REPO_DIR"

test $# -gt 0 || set help

cmd=$1
opt1=$2
opt2=$3
shift

denormalize()
{
    echo $1 | cut -c 2-
}

case $cmd in
    list-tags)
        tags=`get_tags`

        if [ "$opt1" = '-h' ]; then
            list_tags_h
        else
            list_tags
        fi
        ;;

    get-latest)
        get_latest
        ;;

    get-type)
        get_type
        ;;

    get-blob)
        get_blob
        ;;

    get-file)
        get_file
        ;;

    get-dir)
        get_dir
        ;;

    list-blobs)
        list_blobs
        ;;

    tokenize-file)
        tokenize_file
        ;;

    untokenize)
        untokenize
        ;;

    parse-defs)
        parse_defs
        ;;

    help)
        echo "Usage: $0 subcommand [args]..."
        exit 1
        ;;

    *)
        echo "$0: Unknown subcommand: $cmd"
        exit 1
esac
