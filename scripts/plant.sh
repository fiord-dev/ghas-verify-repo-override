#!/usr/bin/env bash
# ダミートークンをファイルに埋め込んでコミットする (push はしない)。
#   usage: scripts/plant.sh <file> <token> [commit message]
#   例   : scripts/plant.sh playground/s1.env "$(scripts/gen_token.py --label s1)"
#   既定は github-pat 形式 (Free プランの org ではカスタムパターンが使えないため)
set -euo pipefail
file=$1 token=$2 msg=${3:-"plant dummy token into $1"}
mkdir -p "$(dirname "$file")"
printf 'DUMMY_TOKEN=%s\n' "$token" >> "$file"
git add "$file"
git commit -q -m "$msg"
git log --oneline -1
