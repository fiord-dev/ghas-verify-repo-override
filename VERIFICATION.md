# GHAS 検証手順

> このリポジトリで使うトークンはすべて `scripts/gen_token.py` がランダムに生成した**無意味な値**です。
> 実在のクレデンシャルは絶対にコミットしないでください。

## 0. 前提: リポジトリ構成

| リポジトリ | 役割 |
| --- | --- |
| `ghas-verify-org-default` | org 全体の Security configuration をそのまま適用 (Dependabot / Code Scanning / Secret Scanning / Push Protection すべて有効) |
| `ghas-verify-repo-override` | 別の Security configuration (またはリポジトリ個別設定) で **Dependabot / Code Scanning を無効化** |

両リポジトリの内容は README 以外同一です。

### org 側の事前設定

1. **Organization settings → Advanced Security → Configurations**
   - `ghas-all-on` (Dependabot alerts / security updates、Code scanning default setup、Secret scanning、Push protection を有効) を作成し、org の全リポジトリに適用・新規リポジトリの既定にする
   - `ghas-no-dependabot-codeql` (Dependabot・Code scanning を無効、Secret scanning / Push protection は有効) を作成し、`ghas-verify-repo-override` のみに適用
   - 確認ポイント: configuration を **Enforce** にすると、リポジトリ側からは変更できなくなります。リポジトリ単位で上書きする検証では、enforce の有無も切り替えて挙動を記録してください。
2. **Organization settings → Advanced Security → Custom patterns** (Secret Protection が必要)
   - ⚠️ **Free プランの org ではカスタムパターンは使えません** (API: `Feature not available in this organization`)。
     その場合は既定の `github-pat` 形式 (`ghp_...`) を使います。public リポジトリは Free プランでもプロバイダーパターンがスキャン対象です。
   - Name: `ghas-verify-dummy`
   - Secret format: `GHASVERIFY_[A-Za-z0-9]{40}`
   - (任意) Before secret: `\A|[^A-Za-z0-9_]` / After secret: `\z|[^A-Za-z0-9]`
   - Dry run で 0 件を確認してから Publish し、**push protection を有効化**する
   - 補足: GitHub 標準パターンの検証には `scripts/gen_token.py --type github-pat` も使えます (チェックサムは正しいが、実在しないトークン)

### 検証中に判明した事項

- `ghp_` 形式のチェックサムは **CRC32 を `0-9A-Za-z` 順の base62 で 6 桁**にしたもの。`0-9a-zA-Z` 順で作った値 (`playground/ss-probe-1.env`) は 10 分待っても検出されなかった → **チェックサムが不正な値は検出対象外**
- リポジトリ設定で push protection を無効 (`secret_scanning_push_protection: disabled`) にしていても、正しい形式の `ghp_` を含む push は `GH013 ... GITHUB PUSH PROTECTION` でブロックされた。
  → 個人設定の「Push protection for yourself」(Settings → Code security、既定で有効) を Disabled にしたところ push 可能になった。**ブロック元は個人設定** (2-0)
- 正しい形式の `ghp_` を push すると、push 直後 (約 1 秒) に Secret scanning アラート #1 (GitHub Personal Access Token, validity: unknown) が作成された

## 1. Security configuration のリポジトリ単位上書き

| # | 確認内容 | 期待 | 結果 |
| --- | --- | --- | --- |
| 1-1 | `org-default` の Security タブに Dependabot alerts が出る (`requirements.txt` / `package.json`) | 出る | |
| 1-2 | `org-default` で Code scanning (CodeQL default setup) が実行され、`app/server.py` / `app/client.js` のアラートが出る | 出る | |
| 1-3 | `repo-override` で Dependabot alerts が出ない (dependency graph の扱いも確認) | 出ない | |
| 1-4 | `repo-override` で CodeQL の workflow run が作成されない | 作成されない | |
| 1-5 | `repo-override` でも Secret scanning / Push protection は有効のまま | 有効 | |
| 1-6 | configuration を enforce した状態で、リポジトリ管理者が設定を変更できるか | | |
| 1-7 | `repo-override` を `ghas-all-on` に付け替えたときに、alert / scan が後から生成されるか | | |

## 2. Push Protection / Secret Scanning のアラート単位

各シナリオで使ったトークンは `.tokens.local` (git 管理外) に記録されます。

```bash
T1=$(scripts/gen_token.py --label s2-1)
```

| # | 操作 | 確認内容 | 結果 |
| --- | --- | --- | --- |
| 2-0 | repo の PP 無効のまま、個人の Push protection for yourself を無効化して push | ブロックされなくなるか (ブロック元の切り分け) | ブロックされなくなった。アラート #1 が即時作成 |
| 2-1 | `scripts/plant.sh playground/a.env "$T1"` → push | Push protection にブロックされるか。ブロック画面でのシークレットの数え方 | |
| 2-2 | 同じ `T1` を `playground/b.env` にも追加し、2 ファイルを 1 回の push に含める | ブロック時の表示は 1 件か、location ごとに 2 件か | ブロック。表示は **1 件** (unblock URL も 1 つ)。locations には 2 ファイルのうち `s2-2-b.env` の 1 箇所のみ表示 |
| 2-3 | `T1` を含むコミット 2 つを積んでまとめて push | コミットごとか、シークレット値ごとか | ブロック。表示は **1 件** (URL 1 つ)。locations は 1 つ目のコミット `s2-3-a.env` の 1 箇所のみ |
| 2-3b | 異なる 2 つの値を 1 コミット・1 回の push に含める | 件数 | **2 件** (値ごとに見出し・location・unblock URL が別々) → **Push protection のブロック単位はシークレット値**。同じ値の出現箇所は代表 1 箇所のみ表示 |
| 2-4 | 2-1 を **bypass (reason: false positive)** で push | bypass 後に生成されるアラートの state / resolution | 理由ごとに別トークンで実施。いずれも bypass 後の再 push で即時アラート作成 (`push_protection_bypassed: true`、bypass 者・日時が記録)。通知メールが 3 理由とも届いた (件名は下表) |

#### 2-4 の詳細: bypass の理由ごとの Secret scanning アラート

| 理由 | アラート | state | resolution | resolved_by | 通知メールの件名 |
| --- | --- | --- | --- | --- | --- |
| It's used in tests | #2 | resolved | `used_in_tests` | bypass した本人 | Secrets bypassed push protection in <repo> |
| It's a false positive | #3 | resolved | `false_positive` | bypass した本人 | Secrets bypassed push protection in <repo> |
| I'll fix it later | #4 | **open** | なし | なし | **Action needed: Secrets detected in <repo>** (本文: "Please resolve these alerts") |

- 「後で修正」だけがアラートを open のまま残す。他の 2 つはアラート作成と同時に resolved になる
- 「後で修正」で bypass した未解決のアラート #4 と同じ値を別ファイルに push → **ブロックされず通過**。アラート #4 に location が追加され、open のまま。新規アラートなし
  → 2-7 (FP クローズ済み) と合わせ、**一度 bypass/アラート化された値は、アラートの state (open/resolved) に関わらず push protection の対象外**になる
- 参考: push protection を通さずに push してから手動で FP クローズしたアラート #1 は `push_protection_bypassed: false`

| 2-5 | 同じ `T1` を別ファイル `playground/c.env` に追加して push | **再度ブロックされるか**。既存アラートに location が追加されるか、新規アラートか | |
| 2-6 | 新しいトークン `T2` を push | 2-4 の FP 判定が別の値に影響しないこと | |
| 2-7 | Push protection を一時的に無効化して `T3` を push → Secret scanning アラートを **Close as false positive** → PP を再有効化して `T3` を別ファイルに push | Secret scanning で FP クローズ済みの値を Push protection がどう扱うか | 個人・org(repo) の PP を有効化後、FP クローズ済みのアラート #1 の値を別ファイル (`TEST_TOKEN=`) に push → **ブロックされず通過**。アラート #1 に location 追加、resolved のまま。対照として新規値を push すると GH013 でブロック → **FP クローズ済みの値は Push protection の対象から外れる** |
| 2-8 | 2-7 の後、PP を無効のまま `T3` を別ファイルに push | FP クローズ済みアラートが reopen されるか / location が増えるか | **reopen されず resolved (false positive) のまま。新規アラートも作られず、既存アラート #1 に location が追加された** (push から約 15 秒) |
| 2-8b | アラート #1 と同じ値を、変数名を `TEST_TOKEN` に変えて別ファイルに push | 変数名 (行の文字列) が変わっても同じアラートとして扱われるか | **同じアラート #1 に location が追加され、resolved (false positive) のまま。新規アラートなし** → アラート/FP 判定の単位は変数名やファイルではなく**シークレット値** |
| 2-9 | `org-default` と `repo-override` に同じ `T4` を push | アラートがリポジトリをまたいで共有されるか (想定: リポジトリ単位) | 先に `repo-override` (repo の PP 無効、個人 PP のみ有効) に push → 個人 PP でブロック。bypass 画面に**理由の選択肢なし**で承認 → 通過し、`repo-override` にアラート #1 (open, `push_protection_bypassed: true`) が作成。**通知メールは届かず**。続けて同じ値を `org-default` に push → **GH013 でブロック** → アラート・push protection の許可は**リポジトリ単位**で、他リポジトリには引き継がれない |
| 2-10 | `T5` を含むコミットを push せずに、`T5` を削除するコミットを積んで両方まとめて push | 履歴中のみに存在するシークレットもブロック対象か | |

### 想定される整理 (検証で確定させる)

- Secret scanning アラート: **リポジトリ × シークレット値** で 1 件。同じ値の出現箇所は location として集約される
- Push protection: push に含まれるコミット中の**シークレット値ごと**にブロック。bypass は値ごとに記録される

## 3. Secret Scanning の除外 (`.github/secret_scanning.yml`)

| # | 操作 | 確認内容 | 結果 |
| --- | --- | --- | --- |
| 3-1 | `scripts/plant.sh secret-scan-excluded/x.env "$T6"` → push | Push protection にブロックされるか | |
| 3-2 | 3-1 が通ったら、Secret scanning アラートが作成されないこと | 作成されない | |
| 3-3 | `playground/excluded-single-file.env` (単一ファイル指定) に `T7` | ファイル単位の除外が効くか | |
| 3-4 | 同じ `T6` を除外外のパス `playground/d.env` にも追加 | アラートの location に除外パスが含まれないか | |
| 3-5 | `secret_scanning.yml` 自体を変更するのと同じ push でトークンを除外パスに追加 | 同一 push での除外設定が反映されるか | |

## 4. Code Scanning: GitHub Actions ワークフロー

`.github/workflows/vuln-*.yml` は、CodeQL (`actions` 言語) に検出させるために意図的に危険な書き方をしたワークフローです。
公開リポジトリで悪用されないよう、全ジョブを `if: false` で止めています。
(`if: github.repository == '...'` のような条件は CodeQL が制御チェックとみなし、untrusted checkout の検出が消えるため使いません)

ローカルの CodeQL CLI 2.27.1 で事前に確認した検出結果:

| ファイル | クエリ | Suite |
| --- | --- | --- |
| `vuln-pr-target-checkout.yml` | Checkout of untrusted code in a privileged context (`actions/untrusted-checkout/*`) | default |
| `vuln-pr-target-checkout.yml` | Excessive Secrets Exposure | default |
| `vuln-pr-target-checkout.yml` | Workflow does not contain permissions | default |
| `vuln-script-injection.yml` | Code injection (`issue.title` / `comment.body` / `GITHUB_ENV` への書き込み) | default |
| `vuln-script-injection.yml` | Unpinned tag for a non-immutable Action | **extended のみ** |
| `vuln-artifact-poisoning.yml` | Artifact poisoning | default |
| `vuln-artifact-poisoning.yml` | Workflow does not contain permissions | default |

| # | 確認内容 | 期待 | 結果 |
| --- | --- | --- | --- |
| 4-1 | `org-default` の Code scanning default setup の言語に `GitHub Actions` が含まれる | 含まれる | |
| 4-2 | 上表のアラートが出る (query suite を Extended にすると unpinned-tag も出る) | 出る | |
| 4-3 | `repo-override` では Actions のアラートも出ない | 出ない | |
| 4-4 | `vuln-*` のワークフローがどのイベントでも実行されない (skipped になる) | skipped | |
