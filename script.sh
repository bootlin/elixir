#!/bin/sh

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2017  Mikaël Bouillot
#  <mikael.bouillot@free-electrons.com>
#
#  Elixir is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#
#  Elixir is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Elixir.  If not, see <http://www.gnu.org/licenses/>.

if [ ! -d "$LXR_REPO_DIR" ]; then
    echo "$0: Can't find repository"
    exit 1
fi

cd "$LXR_REPO_DIR"

test $# -gt 0 || set help

cmd=$1
shift

case $cmd in
    list-tags)
        git tag |
        sort $1 -V
        ;;

    get-type)
        git cat-file -t $1:$2 2>/dev/null
        ;;

    get-blob)
        git cat-file blob $1
        ;;

    get-file)
        git cat-file blob $1:$2 2>/dev/null
        ;;

    get-dir)
        git ls-tree -l "$1:$2" 2>/dev/null |
        awk '{print $2" "$5" "$4}' |
        grep -v ' \.' |
        sort -t ' ' -k 1,1r -k 2,2
        ;;

    list-blobs)
        if [ "$1" = '-p' ]; then
            format='\1 \2'
            shift
        elif [ "$1" = '-f' ]; then
            format='\1 \4'
            shift
        else
            format='\1'
        fi

        git ls-tree -r "$1" |
        sed -r "s/^\S* blob (\S*)\t(([^/]*\/)*(.*))$/$format/"
        ;;

    tokenize-file)
        if [ "$1" = -b ]; then
            ref=$2
        else
            ref=$1:$2
        fi

        git cat-file blob $ref 2>/dev/null |
        tr '\n%<>{}' '\1\2\3\4\5\6' |
        sed 's/\/\*/</g' |
        sed 's/\*\//>/g' |
        sed 's/\\"/%/g' |
        sed 's/"\([^"]*\)"/{\1}/g' |
        sed 's/%/\\"/g' |
        tr '\2' '%' |
        sed -r 's/(\W*)(<[^>]*>)?(\{[^}]*\})?(\w*)/\1\2\3\n\4\n/g' |
        head -n -1
        ;;

    untokenize)
        tr -d '\n' |
        sed 's/>/\*\//g' |
        sed 's/</\/\*/g' |
        tr '\1\2\3' '\n<>'
        ;;

    parse-defs)
        tmp=`mktemp -d`
        git cat-file blob "$1" > $tmp/$2
        ctags -x --c-kinds=+p $tmp/$2 | awk '{print $1" "$2" "$3}'
        rm $tmp/$2
        rmdir $tmp
        ;;

    help)
        echo "Usage: $0 subcommand [args]..."
        exit 1
        ;;

    *)
        echo "$0: Unknown subcommand: $cmd"
        exit 1
esac
