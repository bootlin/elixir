# Xen hypervisor

version_dir()
{
    grep "^RELEASE" |
    sed -e 's/^RELEASE-/v/';
}

version_rev()
{
    grep "^v" |
    sed -e 's/^v/RELEASE-/';
}
