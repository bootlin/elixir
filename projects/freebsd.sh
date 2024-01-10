# FreeBSD

version_dir()
{
    grep "^release/[0-9]*\.[0-9]*\.[0-9]*$" |
    sed -e 's,^release/,v,' |
    sed -e 's,\.0$,,';
}

version_rev()
{
    grep "^v" |
    sed -e 's,v[0-9]*\.[0-9]*$,&\.0,' |
    sed -e 's,^v,release/,';
}
