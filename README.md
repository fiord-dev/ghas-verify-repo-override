# ghas-verify-repo-override

GitHub Advanced Security (Dependabot / Code Scanning / Secret Scanning / Push Protection) の挙動検証用リポジトリです。

**役割:** リポジトリ単位で別の Security configuration を適用し、Dependabot / Code Scanning を無効化するリポジトリ

対になるリポジトリ: [`ghas-verify-org-default`](../ghas-verify-org-default)

> ⚠️ このリポジトリには、意図的に脆弱な依存関係とコードが含まれています。実行・再利用しないでください。
> シークレットはすべてランダム生成された無意味な値です (`scripts/gen_token.py`)。

## 構成

| パス | 目的 |
| --- | --- |
| `requirements.txt`, `package.json` | Dependabot alerts を発生させる古い依存関係 |
| `app/server.py`, `app/client.js` | CodeQL に検出させる脆弱なコード |
| `.github/dependabot.yml` | Dependabot version updates |
| `.github/secret_scanning.yml` | Secret scanning の除外パス設定 |
| `secret-scan-excluded/` | 除外対象ディレクトリ |
| `playground/` | ダミートークンを置く場所 |
| `scripts/gen_token.py` | ダミートークン生成 (`custom` / `github-pat`) |
| `scripts/plant.sh` | トークンをファイルに追記してコミット |

検証手順は [VERIFICATION.md](VERIFICATION.md) を参照してください。
