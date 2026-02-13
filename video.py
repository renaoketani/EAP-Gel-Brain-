import pandas as pd
import cv2
import numpy as np
import os
import glob
import time
from scipy import optimize as opt

def create_replay_video(combine_pong_1751):
    if not os.path.exists(combine_pong_1751):
        print(f"【エラー】ファイルが見つかりません: {combine_pong_1751}")
        return

    print(f"【1/4】ファイルを読み込み中: {combine_pong_1751} ...")
    try:
        df = pd.read_csv(combine_pong_1751)
        df.columns = df.columns.str.strip()
        total_rows = len(df)
        print(f" -> 読み込み完了: {total_rows} 行のデータがあります。")
    except Exception as e:
        print(f"【エラー】CSV読み込みに失敗しました: {e}")
        return

    # --- 設定: 現実の34分を正確に再現する (100Hz -> 30fps) ---
    data_freq = 100        # 1秒間に100行
    fps = 30               # 動画は30枚/秒
    draw_size = 600
    graph_size = 600
    y_min, y_max = -15, 10
    display_sec = 60
    history_rows = data_freq * display_sec

    # データ抽出
    c_blk, c_brn, c_red = df['cBlack'].values, df['cBrown'].values, df['cRed'].values
    b_x, b_y = df['BallX'].values, df['BallY'].values
    
    # RallyCount または RellyCount を探す
    relly_col = next((c for c in df.columns if c.lower().replace(' ', '') in ['rellycount', 'rallycount']), None)
    r_counts = df[relly_col].values if relly_col else np.zeros(total_rows)

    # パドル再現設定
    ORIG_H, P_HEIGHT = 1000, 333
    X_SENSORS = np.array([166, 500, 833])
    DISP_X = np.linspace(0, ORIG_H, 50)

    def map_current_fixed(val):
        temp = (val - (-10)) / (0 - (-10))
        return max(0.0, min(1.0, temp))

    def fit_func(x, a, b, c):
        return a * np.power(x, 2) + b * x + c

    # 動画出力設定
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_name = f"{os.path.splitext(combine_pong_1751)[0]}_realtime_sync.mp4"
    out = cv2.VideoWriter(output_name, fourcc, fps, (draw_size + graph_size, draw_size))
    
    if not out.isOpened():
        print("【エラー】動画ファイルを作成できません。フォルダの書き込み権限を確認してください。")
        return

    print(f"【2/4】動画作成を開始します (出力先: {output_name})")

    # グラフ背景（グリッドのみ）
    bg_base = np.full((draw_size, graph_size, 3), (255, 255, 255), dtype=np.uint8)
    m_l, m_r, m_t, m_b = 65, 30, 70, 65
    g_w, g_h = graph_size - m_l - m_r, draw_size - m_t - m_b
    for v in range(int(y_min), int(y_max) + 1):
        py = draw_size - m_b - int((v - y_min) / (y_max - y_min) * g_h)
        cv2.line(bg_base, (m_l, py), (graph_size - m_r, py), (240, 240, 240), 1)
        cv2.putText(bg_base, str(v), (m_l - 35, py + 5), 1, 0.8, (0,0,0), 1)

    start_t = time.time()
    current_idx_float = 0.0

    # --- 3/4 メインループ ---
    while int(current_idx_float) < total_rows:
        idx = int(current_idx_float)
        
        # パドル位置計算
        try:
            ydata = np.array([map_current_fixed(c_blk[idx]), map_current_fixed(c_brn[idx]), map_current_fixed(c_red[idx])])
            popt, _ = opt.curve_fit(fit_func, X_SENSORS, ydata, maxfev=500)
            raw_pos = DISP_X[np.argmax(fit_func(DISP_X, *popt))] - (P_HEIGHT / 2)
            paddle_y = int(max(0, min(ORIG_H - P_HEIGHT, raw_pos)))
        except:
            paddle_y = 333

        # 1000x1000 ゲーム画面
        game_f = np.full((ORIG_H, ORIG_H, 3), (255, 186, 111), dtype=np.uint8)
        cv2.line(game_f, (500, 0), (500, 1000), (0, 0, 0), 3)
        for h in [333, 666]: cv2.line(game_f, (0, h), (1000, h), (0, 0, 0), 3)
        cv2.rectangle(game_f, (10, paddle_y), (35, paddle_y + P_HEIGHT), (255, 255, 255), -1)
        cv2.rectangle(game_f, (int(b_x[idx]), int(b_y[idx])), (int(b_x[idx])+35, int(b_y[idx])+35), (255, 255, 255), -1)
        cv2.putText(game_f, str(int(r_counts[idx])), (470, 90), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)
        game_f = cv2.resize(game_f, (draw_size, draw_size))

        # グラフ画面
        graph_f = bg_base.copy()
        ts = idx / data_freq
        d_start = max(0, ts - display_sec)
        
        # 波形プロット
        p_idx = np.arange(max(0, idx - history_rows), idx + 1, 4) 
        if len(p_idx) > 1:
            x_pts = (m_l + (p_idx / data_freq - d_start) / display_sec * g_w).astype(np.int32)
            for d, col in [(c_blk, (0,0,0)), (c_brn, (42,42,165)), (c_red, (0,0,255))]:
                y_pts = (draw_size - m_b - ((d[p_idx] - y_min) / (y_max - y_min) * g_h)).astype(np.int32)
                cv2.polylines(graph_f, [np.column_stack([x_pts, y_pts])], False, col, 1, cv2.LINE_AA)

        # 四角い枠線を波形の上に描画
        cv2.rectangle(graph_f, (m_l, m_t), (draw_size - m_r, draw_size - m_b), (0, 0, 0), 2)
        cv2.putText(graph_f, f"Time: {ts:.1f}s", (m_l, m_t - 15), 1, 1.2, (0,0,0), 1)

        out.write(np.hstack((game_f, graph_f)))
        
        current_idx_float += (data_freq / fps)

        # エラーが起きていた進捗表示部分を修正
        if idx % 1000 == 0:
            prog = (idx / total_rows) * 100
            elapsed = time.time() - start_t
            eta = (elapsed / (idx + 1)) * (total_rows - idx) if idx > 0 else 0
            print(f"\r進捗: {prog:5.1f}% | フレーム: {idx}/{total_rows} | 残り: {int(eta)}秒 ", end="")

    out.release()
    print(f"\n【4/4】完了: {output_name}")

if __name__ == "__main__":
    files = glob.glob("*combine*.csv")
    if files:
        target = max(files, key=os.path.getctime)
        create_replay_video(target)
    else:
        print("CSVファイルが見つかりません。")