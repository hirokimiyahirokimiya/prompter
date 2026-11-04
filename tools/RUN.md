# プロンプター同期の手順（定期タスク・「反映して」のときに実行）

合言葉は環境変数 `PROMPTER_PASS='みにりふと'` で渡す。原稿の平文はリポジトリに入れない（コミットするのは script.enc.json と edits.enc.json だけ）。

## 0. 対象
- Mac の接続フォルダ（今の発表）: `/Users/miyashitahiroki/Dropbox/⚫︎学会全般/発表/⚫︎2026/JSAPSミニリフト`
- 対象のパワポ: そのフォルダ直下で、名前が「~$」で始まらず、「発表素案」を含み「.pptx」で終わるファイルのうち mtimeMs が最大のもの
- 期間: 2026-11-07 まで

## 1. 準備
1. device_list_dir（recursive=false）でフォルダを見て、対象のパワポ（名前と mtimeMs）と、フォルダ直下の .pptx の名前一覧を控える。Mac につながらなければ「Mac未接続」で終了。
2. add_repo（hirokimiyahirokimiya/prompter, access: push）→ `git clone --depth 1` → リポジトリのルートへ。
3. `PROMPTER_PASS=... node tools/box.mjs open edits.enc.json /tmp/edits.json`（edits.enc.json が無ければ編集なし）。

## 2. スマホで直した文がある場合（/tmp/edits.json の edits が1件以上）
1. 対象のパワポを device_stage_files で取り込む。
2. `python3 tools/apply_edits.py "<取り込んだpptx>" /tmp/edits.json /mnt/user-data/outputs <フォルダ直下の.pptx名を全部>`
   → JSON レポート（applied / already / conflicts / out）。
3. `out` があれば、その新しい版を device_commit_files で同じフォルダに書き込む（devicePath = フォルダ/out の名前、stagedPath = /mnt/user-data/outputs/out の名前）。古い版は動かさない・消さない。
   書き込んだら device_list_dir でその新ファイルの mtimeMs を取り、これを以降の「対象のパワポ」とする。
4. edits.enc.json を作り直す: 中身は `{"edits":[conflicts に入ったスライドの元の編集だけ], "conflicts":[レポートの conflicts], "applied":[applied+already]}` を /tmp/left.json に書き、`node tools/box.mjs close /tmp/left.json edits.enc.json`。
5. 手順3へ（新しい版から原稿を作る）。

## 3. 原稿の更新
1. script.enc.json の "srcMtime" が対象パワポの mtimeMs と同じで、手順2で何も書き込んでいなければ「変更なし」で終了。
2. 対象パワポ（手順2で作った版なら /mnt/user-data/outputs のもの、そうでなければ device_stage_files で取り込んだもの）で
   `python3 tools/extract_notes.py "<pptx>" /tmp/notes.json <mtimeMs>`
   `PROMPTER_PASS=... node tools/seal.mjs /tmp/notes.json script.enc.json`（終了コード3＝ノート変化なし）
3. 変わったファイル（script.enc.json / edits.enc.json）だけを、作者 hirokimiyahirokimiya <hirokimiya@gmail.com> でコミットして main に push。
   push が競合したら `git pull --rebase` してからもう一度 push（スマホが edits.enc.json を更新していることがある。その場合は手順1.3からやり直す）。
4. 1行で結果を書く。例「v20を作成（スライド3・7を反映、スライド4はパワポ側と競合）」「原稿を更新：v19・24枚」「変更なし」。
