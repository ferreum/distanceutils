#!/usr/bin/bash

usage() {
  cat <<EOM
Usage: ${0##*/} [REPO]
  REPO - Git repository containing the level .bytes files.

  Copies level files used for tests from the given git repository.
EOM
}

mypath=$(dirname -- "$0")

if [[ -z $1 ]]; then
  echo "${0##*/}: missing source repository" >&2
  usage >&2
  exit 1
fi

gitrepo=$1

mapfile -t files <"$mypath/files" || exit 1
mapfile -t githashes <"$mypath/githashes" || exit 1

tmpfile=$(mktemp) || exit 1

cleanup() {
  rm -f -- "$tmpfile"
}
trap cleanup EXIT

errors=0
for (( i = 0; i < ${#files[@]}; i++ )); do
  file=${files[$i]}
  githash=${githashes[$i]}

  destfile=$mypath/$file

  if git -C "$gitrepo" cat-file blob "$githash" >"$tmpfile"; then
    filedir=$(dirname -- "$destfile")
    mkdir -p -- "$filedir"
    if ! cat <"$tmpfile" >"$destfile"; then
      echo "${0##*/}: error writing $destfile" >&2
      (( ++errors ))
    fi
  else
    echo "${0##*/}: blob $githash (${file}) not found in repository '$gitrepo'" >&2
    (( ++errors ))
  fi
done

(( errors == 0 ))

# vim:set sw=2 ts=2 sts=0 et sta sr ft=sh fdm=marker:
