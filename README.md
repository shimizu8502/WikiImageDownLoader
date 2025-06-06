# Pukiwiki画像ダウンローダー

PukiwikiのURLリストから埋め込み画像ファイルを取得して保存するWindowsGUIアプリケーションです。

## 機能

- PukiwikiページのURLリストから全ページにアクセス
- 各ページから.png/.jpg画像を自動抽出
- 指定フォルダに画像を一括保存
- リアルタイムログ表示
- プログレスバー表示
- ダウンロード停止機能
- 設定の自動保存・復元（URL、保存先フォルダ）

## 必要な環境

- Windows 10/11
- Python 3.7以上

## インストール方法

1. 必要なライブラリをインストール:
```bash
pip install -r requirements.txt
```

## 使用方法

1. アプリケーションを起動:
```bash
python wiki_image_downloader.py
```

2. PukiwikiのページリストURL（例：`http://example.com/pukiwiki/?cmd=list`）を入力

3. 保存先フォルダを指定（デフォルト：`./images`）

4. 「ダウンロード開始」ボタンをクリック

5. ログ画面でダウンロード状況を確認

## 動作仕様

1. 指定URLからページリストを取得
2. href属性で指定されている全URLにアクセス
3. 各ページから`<img>`タグの画像URLを抽出
4. .png/.jpgファイルのみをダウンロード
5. 以下の画像ファイルは自動的にスキップされます：
   - backup_*.png, copy_*.png, diff_*.png, edit_*.png
   - file_*.png, freeze_*.png, help_*.png, index_*.png
   - list_*.png, new_*.png, pukiwiki_*.png, recentchanges_*.png
   - reload_*.png, rename_*.png, rss_*.png, search_*.png
   - smile_*.png, top_*.png, unfreeze_*.png
6. 既に同名ファイルが存在する場合はスキップ（上書きしない）

## 注意事項

- サーバーへの負荷軽減のため、各ページアクセス間に0.5秒の待機時間があります
- ネットワークエラーや画像取得エラーは個別にログに記録され、処理を続行します
- 「停止」ボタンで任意のタイミングでダウンロードを中断できます
- Pukiwiki特有の動的URL（plugin=ref、plugin=attach）にも対応しています
- 画像ダウンロード時は適切なリファラーヘッダーを送信します
- 設定は自動的に`settings.ini`ファイルに保存され、次回起動時に復元されます

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。 


## その他 Pukiwiki変換アプリ
- PukiWiki to Markdown Converter
GitHub https://github.com/shimizu8502/WikiMarkDownConverter

