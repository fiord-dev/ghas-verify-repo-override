#!/usr/bin/env bash
# ダミートークンをファイルに埋め込んでコミットする (push はしない)。
#   usage: [VAR=NAME] scripts/plant.sh <file> <token> [commit message]   (VAR の既定は DUMMY_TOKEN)
#   例   : scripts/plant.sh playground/s1.env "$(scripts/gen_token.py --label s1)"
#   既定は github-pat 形式 (Free プランの org ではカスタムパターンが使えないため)
set -euo pipefail
file=$1 token=$2 msg=${3:-"plant dummy token into $1"}
mkdir -p "$(dirname "$file")"
printf '%s=%s\n' "${VAR:-DUMMY_TOKEN}" "$token" >> "$file"
git add "$file"
git commit -q -m "$msg"
git log --oneline -1
