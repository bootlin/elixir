# Elixir definitions for Linux

# Enable DT bindings compatible strings support
dts_comp_support=1

get_tags()
{
    # For repositories with more than mainline, stable, and history remotes many unwanted tags will be present and indexed
    # Operator can specify actual `git tag` command-line arguments or alternatively the special word "kernel.org"
    # in which case a pre-set tag list filter will be used that selects Linux kernel mainline, stable, and history repository tags
    tag_args=""
    if [ -n "${LXR_GIT_TAG_FILTER}" ]; then
      if [ "${LXR_GIT_TAG_FILTER}" = "kernel.org" ]; then
        tag_args="--list ?.? ?.?? ?.?.? ?.??.? ?.??.?? ?.??.??pre* ?.??.??? ?.?.??pre* ?.?.???pre* ?.??.??pre*  ?.??.???pre* v?.? v?.?? v?.?.? v?.?.?? v?.?.??? v?.??.? v?.??.?? v?.??.??? v?.?-rc? v?.??-rc?"
      else
          tag_args="--list ${LXR_GIT_TAG_FILTER}"
      fi
    fi
    git tag ${tag_args} |
    version_dir |
    sed -r 's/^(pre|lia64-|)(v?[0-9\.]*)(pre|-[^pf].*?|)(alpha|-[pf].*?|)([0-9]*)(.*?)$/\2#\3@\4@\5@\60@\1.0/' |
    sort -V |
    sed -r 's/^(.*?)#(.*?)@(.*?)@(.*?)@(.*?)0@(.*?)\.0$/\6\1\2\3\4\5/'
}

list_tags_h()
{
    echo "$tags" |
    tac |
    sed -r 's/^(pre|lia64-|)(v?)([0-9]*)\.([0-9]*)(.*)$/v\3 v\3.\4 \1\2\3.\4\5/'
}
