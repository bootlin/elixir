#!/bin/bash

set -e

clean_git_worktree() {
    find $1 -mindepth 1 -maxdepth 1 -type d -not -path "$1/.git*" -exec rm -r {} \; || true
    find $1 -mindepth 1 -maxdepth 1 -type f -not -path "$1/.git*" -exec rm -r {} \; || true
}

copy_git_worktree() {
    rsync -q -av $1 --exclude .git $2
}

resolve_path() {
    project_path_resolved=`readlink -m $1`
    echo ./`realpath -m --relative-to=$(pwd) $project_path_resolved`
}

print_readme() {
    echo "This directory contains projects specified in west.yaml."
    echo "It was generated automatically and is not a part of the upstream $PROJECT_NAME repository."
    echo "You can report bugs (ex. missing west.yaml projects) at https://github.com/bootlin/elixir"
}

for dep in "west" "rsync" "yq"; do
    if [[ ! "$(command -v $dep)" ]]; then
        echo "$dep is not installed"
        exit 1
    fi
done

if [[ "$#" -ne 1 ]]; then
    echo "usage: $0 west-project-dir"
    exit 1
fi

if ! command -v west 2>&1 >/dev/null; then
    echo "west command is not available"
    exit 1
fi

cd $1

PROJECT_NAME=zephyr
TOP_DIR=./west-topdir
REPO_DIR=./repo
TMP_DIR=./tmp
MAIN_BRANCH=main
export ZEPHYR_BASE=$TOP_DIR

if [[ ! -d $REPO_DIR ]]; then
    echo "$REPO_DIR does not exist. Please clone project repository to $REPO first."
    exit 1
fi

git -C $REPO_DIR config user.email elixir@bootlin.com
git -C $REPO_DIR config user.name "west repository converter for $PROJECT_NAME"

if [[ ! -f $TOP_DIR/$PROJECT_NAME/.git ]]; then
    git -C $REPO_DIR worktree add -f ../$TOP_DIR/$PROJECT_NAME $MAIN_BRANCH
fi

if [[ ! -f $TMP_DIR/.git ]]; then
    git -C $REPO_DIR worktree add -f ../$TMP_DIR $MAIN_BRANCH
    git -C $TMP_DIR checkout --orphan elixir
    git -C $TMP_DIR commit --allow-empty -m "initial commit"
fi

if [[ ! -d $TOP_DIR/.west ]]; then
    west init $TOP_DIR/zephyr -l
fi

project_tags=`git -C $REPO_DIR tag | grep -v "^elixir" | grep -v "^$PROJECT_NAME"`
local_tags=`git -C $REPO_DIR tag | { grep "^elixir" || true; } | sed 's/^elixir-//'`
new_tags=`echo $project_tags $local_tags | tr ' ' '\n' | sort -n | uniq -u`

for tag in $new_tags; do
    echo "found missing tag $tag"
    git -C $TOP_DIR/$PROJECT_NAME checkout -f $tag
    clean_git_worktree $TMP_DIR

    west_manifest=$TOP_DIR/$PROJECT_NAME/west.yml
    if [[ -f $west_manifest ]]; then
        # Find disabled groups
        extra_group_names=`cat west-topdir/$PROJECT_NAME/west.yml | yq -r '(.manifest."group-filter" // [])[]'`
        # Take only disabled groups (start with '-'), enable them (replace - with +),
        # concatenate lines to group-a,group-b,...
        extra_groups=`echo $extra_group_names | tr ' ' '\n' | grep '^-' | sed 's/^-/+/' | paste -s -d,`
        west update $([[ ! -z $extra_groups ]] && echo --group-filter "$extra_groups")
        # Get module paths to copy
        module_paths=`cat $west_manifest | yq -r '.manifest.projects | map(.path)[] | select(. != null)'`

        mkdir -p $TMP_DIR/west_projects
        for top_path in $module_paths; do
            # Check if project_path does not traverse outside west_projects
            project_path=`resolve_path $TMP_DIR/west_projects/$top_path`
            if [[ $project_path =~ ^$TMP_DIR/west_projects/.* ]]; then
                echo "copying $top_path project directory"
                mkdir -p $project_path
                copy_git_worktree $TOP_DIR/$top_path/ $project_path
            else
                echo "found suspicious path $project_path, not copying"
            fi
        done

        print_readme > $TMP_DIR/west_projects/README.txt
    fi

    echo "copying $PROJECT_NAME directory"
    git -C $TMP_DIR checkout -q elixir
    copy_git_worktree $TOP_DIR/$PROJECT_NAME/ $TMP_DIR

    echo "commiting $tag"
    git -C $TMP_DIR add '*'
    git -C $TMP_DIR commit -q -a -m $tag
    git -C $TMP_DIR tag elixir-$tag
done

