#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

usage() {
  echo "Usage: $0 save <folder> [-a] [image ...]" >&2
  echo "       $0 restore <folder>" >&2
  echo "  With no images listed, save exports named images only (podman images -q)." >&2
  echo "  -a exports everything, including untagged/build-cache images (podman images -a -q)." >&2
  exit 1
}

[ $# -ge 2 ] || usage
action=$1
dir=${2%/}   # strip any trailing slash so "$dir/..." stays single-slash everywhere
shift 2

case "$action" in
  save)
    mkdir -p "$dir"
    if [ -n "$(ls -A "$dir")" ]; then
      echo "WARNING: $dir is not empty — existing files may be left stale or mixed in with this run's output." >&2
      read -r -p "Press Enter to continue, or Ctrl-C to abort: "
    fi

    # id -> space-separated list of its current repo:tag names. Derived from
    # ONE json snapshot so id formatting is consistent by construction — the
    # previous mix of -q / -a -q / --no-trunc / --format template disagreed
    # on truncation and sha256: prefixing in ways that silently broke
    # lookups (twice). Images with no names contribute nothing here, same
    # effect as the old <none>:<none> filter.
    declare -A tags_for_id=()
    while IFS=$'\t' read -r id name; do
      id=${id#sha256:}
      tags_for_id[$id]="${tags_for_id[$id]:-} $name"
    done < <(podman images -a --format json \
               | jq -r '.[] | .Id as $id | (.Names // [])[] | [$id, .] | @tsv')

    all=false
    if [ "${1:-}" = "-a" ]; then
      all=true
      shift
    fi

    if [ $# -gt 0 ]; then
      mapfile -t ids < <(for ref in "$@"; do podman image inspect --format '{{.Id}}' "$ref"; done | sort -u)
    elif [ "$all" = true ]; then
      mapfile -t ids < <(podman images -a --format json | jq -r '.[].Id | sub("^sha256:";"")' | sort -u)
    else
      mapfile -t ids < <(podman images -a --format json \
                            | jq -r '.[] | select((.Names // []) | length > 0) | .Id | sub("^sha256:";"")' \
                            | sort -u)
    fi

    total=${#ids[@]}
    n=0
    for id in "${ids[@]}"; do
      n=$((n+1))
      out="$dir/$id.tar"
      if [ -e "$out" ]; then
        echo "[$n/$total] WARNING: $out already exists, skipping save (names still (re)linked below)" >&2
      else
        echo "[$n/$total] saving $id -> $out"
        podman save --format oci-archive -o "$out" "$id"
      fi

      # One symlink per known name -> id.tar, nested to match the name's own
      # slashes (e.g. localhost/python-nodejs:latest, or
      # docker.io/jupyter/scipy-notebook:notebook-6.5.4). This is both for
      # tracing and the source of truth restore uses to re-tag explicitly —
      # it's what makes multiple names sharing one id survive correctly,
      # and it's refreshed even when the tar above already existed.
      for name in ${tags_for_id[$id]:-}; do
        linkdir="$dir/$(dirname "$name")"
        mkdir -p "$linkdir"
        target=$(realpath --relative-to="$linkdir" "$out")
        ln -sfn "$target" "$dir/$name"
      done
    done
    echo "done: saved $n image(s) to $dir"
    ;;

  restore)
    [ -d "$dir" ] || { echo "ERROR: $dir does not exist" >&2; exit 1; }
    files=("$dir"/*.tar)
    if [ ${#files[@]} -eq 0 ]; then
      echo "ERROR: no .tar files found in $dir" >&2
      exit 1
    fi

    # saved id (from the filename) -> id actually assigned by this load.
    # podman save/load through oci-archive can change the id: for images
    # that originated from a registry's multi-arch manifest list (e.g.
    # quay.io/jupyter/*), the config gets re-encoded on save, so its digest
    # - and hence the image id - differs after load. Never assume the
    # filename's id survived; always use what `podman load` reports.
    declare -A actual_id=()
    n=0
    total=${#files[@]}
    for f in "${files[@]}"; do
      n=$((n+1))
      echo "[$n/$total] loading $f"
      saved_id=$(basename "$f" .tar)
      loaded=$(podman load -i "$f")
      echo "$loaded"
      new_id=$(sed -n 's/^Loaded image: sha256:\([0-9a-f]*\)/\1/p' <<< "$loaded" | tail -n1)
      actual_id[$saved_id]=${new_id:-$saved_id}
    done
    echo "done: loaded $n image(s) from $dir"

    # Explicitly (re)apply every known name from the symlinks — this is the
    # actual tag-restoration mechanism, independent of whatever the archive
    # itself did or didn't embed.
    n=0
    while IFS= read -r -d '' link; do
      target=$(readlink -f "$link") || continue
      if [ ! -e "$target" ]; then
        echo "WARNING: $link -> $target is dangling, skipping" >&2
        continue
      fi
      saved_id=$(basename "$target" .tar)
      id=${actual_id[$saved_id]:-$saved_id}
      name=${link#"$dir"/}
      n=$((n+1))
      echo "tagging $id as $name"
      podman tag "$id" "$name"
    done < <(find "$dir" -mindepth 1 -type l -print0)
    echo "done: applied $n name(s) from symlinks"
    ;;

  *)
    usage
    ;;
esac
