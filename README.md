# EAPゲルを用いた制御コード

本リポジトリは，2025年度 立命館大学 理工学部 ロボティクス学科 クラウドロボティクス研究室における卒業論文「EAPゲルを用いた『Gel Brain』のインターフェイス構築」で使用した制御プログラム一式を管理するものです．

## 概要
以下の2つの主要実験で用いた制御コードを含みます．
- **1 Stimulation / 3 Sensing制御**: 1つの刺激(Stimulation)電極と3つの計測(Sensing)電極の制御
- **Pong Game制御**: EAPゲルをインターフェイスとしたPong Gameのリアルタイム制御・実行

## 使用言語・ライブラリ
* Python 3.x
* Pygame (ゲーム画面・シミュレーション用)
* Matplotlib / Pandas / Seaborn (データ解析・グラフ生成用)
* OpenCV (動画生成用)

## ファイル構成

### 1. 1 Stimulation / 3 Sensing 実験
* `relay_ina_1.py`: 先行研究で使用されていたリレー2連回路の制御．1 Stimulation/3 Sensing電極の制御および電流値測定．
* `tra_ina_1.py`: 本研究で新規開発した2段構成トランジスタ回路の制御．1 Stimulation/3 Sensing電極の制御および電流値測定．

### 2. Pong Game 実験 (traフォルダ相当)
本研究のトランジスタ回路を用いた，Pong Game実行用プログラム群です．
* `tra_main.py`: **システム全体実行用．** センサデータ取得，ゲーム実行，ゲルとゲーム情報の同期保存を並行管理．
* `tra_plotter.py`: センサデータ取得およびRaspberry PiのGPIOを介した電極印加の制御．
* `pong.py`: ゲーム画面の描画，センサデータの座標変換によるパドル制御，ボール領域判定に基づく電極指示．
* `ball.py`: ボールの挙動定義（速度計算，壁面・パドル衝突時の反射角度のランダム計算）．
* `paddle.py`: センサ入力値に基づいたパドルの挙動定義．
* `region.py`: ゲーム画面の領域分割（6分割）．ボール侵入感知および刺激フィードバックの判断領域定義．
* `config.py`: センサ，リレー，ボール動作制御に係る通信キュー名称の一元管理（保守性向上用）．

### 3. Random刺激比較実験 (randomフォルダ相当)
Pong Game中にランダム刺激を加え，ゲルの挙動・反応変化を確認する実験用プログラムです．
* `main_random_tra.py`: 通常モードとランダム刺激モードを一定時間ごとに切り替え，学習効果や反応変化を比較検証するメインプログラム．
* `plotter_random_tra.py`: 3つのセンサによるデータ取得および実験モードに応じた刺激出力の並行実行．
* `pong_random_tra.py`: 2つのモードに対応したゲームロジック．ボール連動刺激の生成および，センサ入力値の2次関数フィッティングによるパドル位置推定機能．

### 4.Pong gameの動画作成
* `video.py`:Pong game実行時に得られた電流値，ボールの座標，パドルの位置，およびラリー回数を含むCSVデータに基づき，ゲームの実行過程を動画として再構成するプログラム．
  
## ソフトウェア環境と実行方法

### 1. 必要なライブラリのインストール
ターミナル（またはコマンドプロンプト）で以下のコマンドを実行してください．

```bash pip install pygame pandas numpy matplotlib seaborn opencv-python adafruit-blinka adafruit-circuitpython-ina219 RPi.GPIO```


### 2. 各ライブラリの用途

システム制御（Raspberry Pi）: adafruit-circuitpython-ina219 (計測)， adafruit-blinka (環境動作)， RPi.GPIO (リレー・回路制御)

シミュレーション: pygame (描画・環境構築)

解析・可視化: pandas． numpy． matplotlib． seaborn

動画生成: opencv-python

### 3. 注意事項（Raspberry Piを使用する場合）
I2C通信を利用するため、あらかじめOS側の設定でI2Cインターフェースを有効化しておく必要があります。

#### I2Cの有効化設定（インターフェース設定からI2CをEnableにしてください）
```bash sudo raspi-config```

#### 接続確認（INA219のアドレス 0x40, 0x41, 0x44 などが表示されれば正常です）
```bash i2cdetect -y 1```

## 著者
*桶谷　怜央

*立命館大学　クラウドロボティクス研究室
