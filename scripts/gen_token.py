#!/usr/bin/env python3
"""検証用の「意味のない」ダミートークンを生成する。

- custom     : org のカスタムパターン用 (GHASVERIFY_ + 40 文字の英数字)。Secret Protection 契約のある org でのみ有効。
- github-pat : GitHub PAT (classic) と同じ形式 (ghp_ + 30 文字 + CRC32 チェックサム 6 文字)。
               ランダム生成のため実在のトークンではないが、GitHub 標準パターンに一致する。既定値。

生成したトークンは .tokens.local (git 管理外) に追記し、同じトークンの再利用
(FP として処理した後の再 push 検証など) に使う。
"""
import argparse
import datetime
import json
import pathlib
import secrets
import string
import zlib

ALPHABET = string.digits + string.ascii_letters  # base62
LOG = pathlib.Path(__file__).resolve().parent.parent / ".tokens.local"


def base62(n: int, width: int) -> str:
    out = ""
    while n:
        n, r = divmod(n, 62)
        out = ALPHABET[r] + out
    return out.rjust(width, "0")


def gen_custom() -> str:
    return "GHASVERIFY_" + "".join(secrets.choice(ALPHABET) for _ in range(40))


def gen_github_pat() -> str:
    body = "".join(secrets.choice(ALPHABET) for _ in range(30))
    return "ghp_" + body + base62(zlib.crc32(body.encode()), 6)


GENERATORS = {"custom": gen_custom, "github-pat": gen_github_pat}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--type", choices=GENERATORS, default="github-pat")
    p.add_argument("--label", default="", help=".tokens.local に記録するラベル")
    args = p.parse_args()

    token = GENERATORS[args.type]()
    with LOG.open("a") as f:
        f.write(json.dumps({
            "at": datetime.datetime.now().isoformat(timespec="seconds"),
            "type": args.type,
            "label": args.label,
            "token": token,
        }) + "\n")
    print(token)


if __name__ == "__main__":
    main()
