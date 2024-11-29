import os
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def create_text_file():
    """日本語音声を含むテストファイル生成スクリプト"""
    
    # ディレクトリ作成
    os.makedirs("test_files", exist_ok=True)
    
    # サンプルテキストファイル作成
    with open("test_files/sample.txt", "w", encoding="utf-8") as f:
        f.write("""これはテスト用のサンプルテキストファイルです。
複数行のテキストが含まれています。
* 1行目：ドキュメントのアップロードのテスト
* 2行目：テキスト処理のテスト
* 3行目：インデックス機能のテスト
* 4行目：検索機能のテスト""")


def create_image_file():
    """テスト用の有意義な画像を生成"""

    # 白背景の画像を作成 (500x300)
    width = 500
    height = 300
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # バーチャートを描画
    data = [50, 80, 60, 90, 70]  # サンプルデータ
    bar_width = 60
    spacing = 30
    start_x = 50
    max_bar_height = 200  # バーの最大高さ
    baseline_y = height - 50  # グラフのベースライン
    
    for i, value in enumerate(data):
        # バーを描画
        x = start_x + (bar_width + spacing) * i
        bar_height = int((value / 100) * max_bar_height)  # パーセンテージを高さに変換
        
        # グラデーションのような効果を出す
        bar_color = (64 + i * 30, 105 + i * 20, 225 - i * 20)  # 青系の色
        
        # バーを描画（y0が上端、y1が下端になるように修正）
        y0 = baseline_y - bar_height  # 上端
        y1 = baseline_y  # 下端
        draw.rectangle(
            [x, y0, x + bar_width, y1],
            fill=bar_color
        )
        
        # 値を描画
        value_x = x + (bar_width // 2) - 10
        draw.text(
            (value_x, baseline_y + 10),
            str(value),
            fill='black'
        )
    
    # タイトルを追加
    title = "Performance Metrics"
    title_x = width // 2 - 60  # タイトルを中央に配置
    draw.text((title_x, 20), title, fill='black')
    
    # X軸のラベル
    labels = ['CPU', 'GPU', 'RAM', 'API', 'DB']
    for i, label in enumerate(labels):
        x = start_x + (bar_width + spacing) * i + (bar_width // 2) - 15
        draw.text((x, height - 25), label, fill='black')
    
    # Y軸
    draw.line([(40, 50), (40, height - 50)], fill='black')
    draw.line([(40, height - 50), (width - 40, height - 50)], fill='black')
    
    # Y軸のメモリ
    for i in range(6):
        y = height - 50 - i * 40
        draw.line([(35, y), (45, y)], fill='black')
        draw.text((10, y - 10), str(i * 20), fill='black')

    img.save("test_files/sample.jpg")


def create_audio_file():
    # 日本語音声ファイル作成
    text = "これはDifyの負荷テスト用の音声ファイルです。音声認識と文字起こしの機能をテストします。"
    tts = gTTS(text=text, lang='ja')
    tts.save("test_files/sample.mp3")

if __name__ == "__main__":
    create_text_file()
    create_image_file()
    create_audio_file()