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

denormalize()
{
    echo $1 | cut -c 2-
}

project=$(basename `dirname $LXR_REPO_DIR`)

case $project in
    busybox)
        version_dir() { tr '_.' '._'; }
        version_rev() { tr '._' '_.'; }
    ;;
    *)
        version_dir() { cat; }
        version_rev() { cat; }
    ;;
esac

case $cmd in
    list-tags)
        tags=$(
            git tag |
            version_dir |
            sed 's/$/.0/' |
            sort -V |
            sed 's/\.0$//'
        )
        if [ "$1" = '-h' ]; then
            case $project in
              linux)
                echo "$tags" |
                tac |
                sed -r 's/^(((v2.6)\.([0-9]*)(.*))|(v[0-9])\.([0-9]*)(.*))$/\3\6 \3\6.\4\7 \3\6.\4\7\5\8/'
              ;;
              u-boot)
                echo "$tags" |
                grep '^v20' |
                tac |
                sed -r 's/^(v20..)(.*)$/new \1 \1\2/'

                echo "$tags" |
                grep -E '^(v1|U)' |
                tac |
                sed -r 's/^/old by-version /'

                echo "$tags" |
                grep -E '^(LABEL|DENX)' |
                tac |
                sed -r 's/^/old by-date /'

              ;;
              busybox)
                echo "$tags" |
                tac |
                sed -r 's/^([0-9])\.([0-9]*)(.*)$/v\1 \1.\2 \1.\2\3/'
              ;;
              *)
                echo "$tags" |
                tac |
                sed -r 's/^/XXX XXX /'
              ;;
            esac
        else
            echo "$tags"
        fi
        ;;

    get-type)
        v=`echo $1 | version_rev`
        git cat-file -t "$v:`denormalize $2`" 2>/dev/null
        ;;

    get-blob)
        git cat-file blob $1
        ;;

    get-file)
        v=`echo $1 | version_rev`
        git cat-file blob "$v:`denormalize $2`" 2>/dev/null
        ;;

    get-dir)
        v=`echo $1 | version_rev`
        git ls-tree -l "$v:`denormalize $2`" 2>/dev/null |
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

        v=`echo $1 | version_rev`
        git ls-tree -r "$v" |
        sed -r "s/^\S* blob (\S*)\t(([^/]*\/)*(.*))$/$format/"
        ;;

    tokenize-file)
        if [ "$1" = -b ]; then
            ref=$2
        else
            v=`echo $1 | version_rev`
            ref="$v:`denormalize $2`"
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
        ctags -x --c-kinds=+p-m $tmp/$2 | awk '{print $1" "$2" "$3}'
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
