# EAPゲルを用いた制御コード

このリポジトリでは、立命館大学 理工学部 ロボティクス学科 クラウドロボティクス研究室で進めている卒業論文に関する研究用コードを管理しています。

## 概要
* **研究目的**: EAPゲルを用いた「Gel Brain」のインターフェイス構築
* **主な機能**: 
  - 1つの刺激(Stimulation)電極と3つの計測(Sensing)電極の制御
  - EAPゲルをインターフェイスとしたPong Gameの制御・実行

## 使用言語・ライブラリ
* Python 3.x
* Pygame (ゲーム画面・シミュレーション用)
* Matplotlib / Pandas / Seaborn (データ解析・グラフ生成用)
* OpenCV (動画生成用)

## ファイル構成
* `videotra.py`: 実験ログ（CSV）から `opencv-python` を用いてビデオ出力を生成するスクリプト
* `pong_game.py`: EAPゲルの入力を反映させ、`pygame` で動作するメインの制御・ゲームプログラム
* `data/`: 実験結果のCSVデータを格納するフォルダ

## ソフトウェア環境と実行方法

### 1. 必要なライブラリのインストール
本研究で開発した制御システムおよび解析プログラムを実行するには、以下のライブラリが必要です。ターミナル（またはコマンドプロンプト）で以下のコマンドを実行してインストールしてください。

```bash
pip install pygame pandas numpy matplotlib seaborn opencv-python adafruit-blinka adafruit-circuitpython-ina219 RPi.GPIO
