# Elixir definitions for glibc

list_tags()
{
    echo "$tags" |
    grep -v 'cvs'
}

list_tags_h()
{
    echo "$tags" |
    grep "glibc" |
    grep -v "fedora" |
    grep -v "cvs" |
    tac |
    sed -r 's/^glibc-([0-9]*)(\.[0-9]*)(.*)$/\1 \1\2 glibc-\1\2\3/'

    echo "$tags" |
    grep -v "cvs" |
    grep "fedora" |
    tac |
    sed -r 's/^fedora\/glibc-([0-9]*)(\.[0-9]*)(.*)$/fedora \1\2 fedora\/glibc-\1\2\3/'
}
