import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
from bs4 import BeautifulSoup
import os
import re
import threading
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
import fnmatch
import configparser


class WikiImageDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Pukiwiki画像ダウンローダー")
        self.root.geometry("800x600")
        
        # 設定ファイルのパス
        self.config_file = "settings.ini"
        
        # ダウンロードを停止するためのフラグ
        self.stop_download = False
        
        # 保存しない画像ファイルリスト
        self.skip_patterns = [
            'backup_*.png', 'copy_*.png', 'diff_*.png', 'edit_*.png',
            'file_*.png', 'freeze_*.png', 'help_*.png', 'index_*.png',
            'list_*.png', 'new_*.png', 'pukiwiki_*.png', 'recentchanges_*.png',
            'reload_*.png', 'rename_*.png', 'rss_*.png', 'search_*.png',
            'smile_*.png', 'top_*.png', 'unfreeze_*.png'
        ]
        
        # 設定を読み込み
        self.load_settings()
        
        self.create_widgets()
        
        # アプリケーション終了時の処理を設定
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # URL入力セクション
        url_frame = ttk.LabelFrame(main_frame, text="URL設定", padding="10")
        url_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(url_frame, text="PukiwikiページURL:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.url_entry = ttk.Entry(url_frame, width=80)
        self.url_entry.insert(0, self.default_url)  # 設定から読み込んだ初期値を設定
        self.url_entry.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # URL変更時の処理を追加
        self.url_entry.bind('<FocusOut>', self.on_url_changed)
        self.url_entry.bind('<KeyRelease>', self.on_url_changed)
        
        # URL例を表示
        example_label = ttk.Label(url_frame, text="例: http://example.com/pukiwiki/?cmd=list", 
                                 foreground="gray")
        example_label.grid(row=2, column=0, columnspan=3, sticky=tk.W)
        
        # 保存先設定
        save_frame = ttk.LabelFrame(main_frame, text="保存設定", padding="10")
        save_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(save_frame, text="保存フォルダ:").grid(row=0, column=0, sticky=tk.W)
        self.save_path_var = tk.StringVar(value=self.default_save_path)
        save_path_entry = ttk.Entry(save_frame, textvariable=self.save_path_var, width=60)
        save_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5))
        
        # 保存先変更時の処理を追加
        self.save_path_var.trace('w', self.on_save_path_changed)
        
        browse_btn = ttk.Button(save_frame, text="参照", command=self.browse_folder)
        browse_btn.grid(row=0, column=2, padx=(5, 0))
        
        # コントロールボタン
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        self.download_btn = ttk.Button(control_frame, text="ダウンロード開始", 
                                      command=self.start_download)
        self.download_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="停止", 
                                  command=self.stop_download_process, state="disabled")
        self.stop_btn.grid(row=0, column=1)
        
        # プログレスバー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # ステータス表示
        self.status_var = tk.StringVar(value="待機中")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # ログ表示
        log_frame = ttk.LabelFrame(main_frame, text="ログ", padding="10")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッドの重みを設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        url_frame.columnconfigure(0, weight=1)
        save_frame.columnconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path_var.set(folder)
            
    def load_settings(self):
        """設定ファイルから設定を読み込み"""
        self.config = configparser.ConfigParser()
        
        # デフォルト値
        self.default_url = "http://192.168.1.167/index.php?cmd=list"
        self.default_save_path = "./images"
        
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file, encoding='utf-8')
                
                # URL設定を読み込み
                if self.config.has_option('Settings', 'pukiwiki_url'):
                    self.default_url = self.config.get('Settings', 'pukiwiki_url')
                
                # 保存先設定を読み込み
                if self.config.has_option('Settings', 'save_path'):
                    self.default_save_path = self.config.get('Settings', 'save_path')
                    
            except Exception as e:
                print(f"設定ファイル読み込みエラー: {e}")
        
        # セクションが存在しない場合は作成
        if not self.config.has_section('Settings'):
            self.config.add_section('Settings')
    
    def save_settings(self):
        """設定をファイルに保存"""
        try:
            # 現在の設定を取得
            current_url = self.url_entry.get().strip()
            current_save_path = self.save_path_var.get().strip()
            
            # 設定を更新
            self.config.set('Settings', 'pukiwiki_url', current_url)
            self.config.set('Settings', 'save_path', current_save_path)
            
            # ファイルに保存
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
                
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")
    
    def on_url_changed(self, event=None):
        """URL変更時の処理"""
        self.save_settings()
    
    def on_save_path_changed(self, *args):
        """保存先変更時の処理"""
        self.save_settings()
    
    def on_closing(self):
        """アプリケーション終了時の処理"""
        self.save_settings()
        self.root.destroy()

    def should_skip_file(self, filename):
        """ファイル名がスキップパターンに該当するかチェック"""
        for pattern in self.skip_patterns:
            if fnmatch.fnmatch(filename.lower(), pattern):
                return True
        return False
            
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def update_status(self, status):
        self.status_var.set(status)
        self.root.update_idletasks()
        
    def update_progress(self, current, total):
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
        self.root.update_idletasks()
        
    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("エラー", "URLを入力してください。")
            return
            
        self.stop_download = False
        self.download_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        
        # 別スレッドでダウンロード処理を実行
        thread = threading.Thread(target=self.download_images, args=(url,))
        thread.daemon = True
        thread.start()
        
    def stop_download_process(self):
        self.stop_download = True
        self.update_status("停止中...")
        self.log_message("ダウンロードを停止しています...")
        
    def download_images(self, base_url):
        try:
            self.update_status("ページリストを取得中...")
            self.log_message("ページリストの取得を開始します")
            
            # ページリストを取得
            page_urls = self.get_page_urls(base_url)
            if not page_urls:
                self.log_message("ページURLが見つかりませんでした")
                return
                
            self.log_message(f"{len(page_urls)}個のページが見つかりました")
            
            # 保存フォルダを作成
            save_path = self.save_path_var.get()
            if not os.path.exists(save_path):
                os.makedirs(save_path)
                self.log_message(f"保存フォルダを作成しました: {save_path}")
            
            # 各ページから画像を取得
            total_images = 0
            processed_pages = 0
            
            for i, page_url in enumerate(page_urls):
                if self.stop_download:
                    break
                    
                self.update_status(f"ページを処理中... ({i+1}/{len(page_urls)})")
                self.update_progress(i, len(page_urls))
                
                try:
                    images = self.extract_images_from_page(page_url)
                    if images:
                        self.log_message(f"ページ {page_url} から {len(images)}個の画像を発見")
                        downloaded = self.download_images_from_page(images, save_path, page_url)
                        total_images += downloaded
                    processed_pages += 1
                    
                except Exception as e:
                    self.log_message(f"ページ処理エラー {page_url}: {str(e)}")
                    
                # 少し待機（サーバーへの負荷軽減）
                time.sleep(0.5)
                
            if not self.stop_download:
                self.update_progress(100, 100)
                self.update_status("完了")
                self.log_message(f"ダウンロード完了: {total_images}個の画像を保存しました")
            else:
                self.update_status("停止")
                self.log_message("ダウンロードが停止されました")
                
        except Exception as e:
            self.log_message(f"エラーが発生しました: {str(e)}")
            self.update_status("エラー")
            
        finally:
            self.download_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            
    def get_page_urls(self, base_url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(base_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # href属性を持つリンクを全て取得
            links = soup.find_all('a', href=True)
            page_urls = []
            
            for link in links:
                href = link['href']
                # 相対URLを絶対URLに変換
                full_url = urljoin(base_url, href)
                
                # Pukiwikiのページらしいかチェック（簡単な判定）
                if ('?' in full_url and 
                    ('cmd=' in full_url or 'page=' in full_url or full_url.count('?') == 1)):
                    page_urls.append(full_url)
                    
            # 重複を削除
            page_urls = list(set(page_urls))
            return page_urls
            
        except Exception as e:
            self.log_message(f"ページリスト取得エラー: {str(e)}")
            return []
            
    def extract_images_from_page(self, page_url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(page_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 画像要素を検索
            img_tags = soup.find_all('img')
            image_urls = []
            
            for img in img_tags:
                src = img.get('src')
                if src:
                    # 相対URLを絶対URLに変換
                    full_url = urljoin(page_url, src)
                    
                    # PNG、JPGファイルのチェック方法を改善
                    # 1. URL末尾での判定
                    # 2. URLパラメータ内での判定（Pukiwiki対応）
                    is_image = False
                    
                    # 通常のURL形式（末尾が画像拡張子）
                    if re.search(r'\.(png|jpg|jpeg)(\?.*)?$', full_url, re.IGNORECASE):
                        is_image = True
                    
                    # Pukiwiki形式のURL（src=ファイル名.拡張子）
                    elif re.search(r'[?&]src=[^&]*\.(png|jpg|jpeg)', full_url, re.IGNORECASE):
                        is_image = True
                    
                    # plugin=attachやplugin=refの場合でファイル名に画像拡張子が含まれる場合
                    elif re.search(r'(plugin=attach|plugin=ref).*\.(png|jpg|jpeg)', full_url, re.IGNORECASE):
                        is_image = True
                    
                    if is_image:
                        image_urls.append(full_url)
                        
            return image_urls
            
        except Exception as e:
            self.log_message(f"画像抽出エラー {page_url}: {str(e)}")
            return []
            
    def extract_filename_from_url(self, img_url):
        """URLから適切なファイル名を抽出"""
        # Pukiwiki形式のURL（src=ファイル名）から抽出
        src_match = re.search(r'[?&]src=([^&]*\.(png|jpg|jpeg))', img_url, re.IGNORECASE)
        if src_match:
            return src_match.group(1)
        
        # openfile=ファイル名の形式から抽出
        openfile_match = re.search(r'[?&]openfile=([^&]*\.(png|jpg|jpeg))', img_url, re.IGNORECASE)
        if openfile_match:
            return openfile_match.group(1)
        
        # 通常のURL形式からファイル名を取得
        parsed_url = urlparse(img_url)
        filename = os.path.basename(parsed_url.path)
        
        # ファイル名が適切でない場合
        if not filename or '.' not in filename:
            # URLから拡張子を推測
            extension = '.png' if 'png' in img_url.lower() else '.jpg'
            timestamp = int(time.time())
            filename = f"image_{timestamp}{extension}"
        
        return filename

    def download_images_from_page(self, image_urls, save_path, page_url):
        downloaded_count = 0
        skipped_count = 0
        
        for img_url in image_urls:
            if self.stop_download:
                break
                
            try:
                # ファイル名を生成
                filename = self.extract_filename_from_url(img_url)
                
                # スキップパターンに該当するかチェック
                if self.should_skip_file(filename):
                    self.log_message(f"画像をスキップ（除外パターン）: {filename}")
                    skipped_count += 1
                    continue
                
                # 保存パスを作成
                file_path = os.path.join(save_path, filename)
                
                # 同名ファイルが存在する場合はスキップ
                if os.path.exists(file_path):
                    self.log_message(f"画像をスキップ（既存ファイル）: {filename}")
                    skipped_count += 1
                    continue
                
                # ファイルをダウンロード（リファラーヘッダーを追加）
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': page_url,  # 元のページをリファラーとして設定
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
                }
                
                self.log_message(f"画像ダウンロード中: {filename} from {img_url}")
                
                img_response = requests.get(img_url, headers=headers, timeout=30)
                img_response.raise_for_status()
                
                # レスポンスが実際に画像データかチェック
                content_type = img_response.headers.get('content-type', '').lower()
                if not content_type.startswith('image/'):
                    # HTMLが返された場合など
                    if 'text/html' in content_type:
                        self.log_message(f"画像URLからHTMLが返されました: {img_url}")
                        skipped_count += 1
                        continue
                
                with open(file_path, 'wb') as f:
                    f.write(img_response.content)
                
                self.log_message(f"画像を保存: {filename} ({len(img_response.content)} bytes)")
                downloaded_count += 1
                
            except Exception as e:
                self.log_message(f"画像ダウンロードエラー {img_url}: {str(e)}")
                
        if skipped_count > 0:
            self.log_message(f"スキップした画像: {skipped_count}個")
            
        return downloaded_count


def main():
    root = tk.Tk()
    app = WikiImageDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main() 