from flask import Flask, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッションを使うために秘密鍵が必要
socketio = SocketIO(app)  # Flask-SocketIOのインスタンス

# リクエストを記録するデータベース（メモリ内で保存）
replay_requests = []

@app.route('/')
def home():
    # セッションに名前があれば、フォームにその名前を事前入力
    player_name = session.get('player_name', '')
    
    return '''
    <h1>Instant Replay Request</h1>
    <!-- 大会ロゴを表示 -->
    <img src="/static/logo.png" alt="Tournament Logo" style="max-width: 300px; height: auto;">
    <form action="/request_replay" method="post">
        <label for="player_name">Player Name:</label>
        <input type="text" id="player_name" name="player_name" value="{}" required>
        <button type="submit">Request Replay</button>
    </form>
    '''.format(player_name)

@app.route('/request_replay', methods=['POST'])
def request_replay():
    # 選手の名前と現在の時刻を取得して記録
    player_name = request.form['player_name']
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    user_ip = request.remote_addr
    replay_requests.append({'timestamp': timestamp, 'player_name': player_name, 'ip': user_ip})
    
    # 名前をセッションに保存
    session['player_name'] = player_name
    
    # 新しいリクエストをリアルタイムでクライアントに通知
    socketio.emit('new_replay', {'timestamp': timestamp, 'player_name': player_name, 'ip': user_ip}, room=None)
    
    return f'Replay requested at {timestamp} from {player_name} ({user_ip}). <a href="/">Back</a>'

@app.route('/admin')
def admin():
    # 管理者画面を表示
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Replay Requests</title>
        <script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
        <script>
            const socket = io();  // WebSocket接続を開始

            socket.on('new_replay', (data) => {
                // 新しいリクエストを受信
                const requestList = document.getElementById('requestList');
                const newItem = document.createElement('li');
                newItem.textContent = `${data.timestamp} - ${data.player_name} (IP: ${data.ip})`;
                requestList.appendChild(newItem);

                // デスクトップ通知を表示
                if (Notification.permission === 'granted') {
                    new Notification('New Replay Request', { body: `At ${data.timestamp} from ${data.player_name}` });
                }
            });

            // ページがロードされたときに通知権限をリクエスト
            document.addEventListener('DOMContentLoaded', () => {
                if (Notification.permission !== 'granted') {
                    Notification.requestPermission();
                }
            });
        </script>
    </head>
    <body>
        <h1>Replay Requests</h1>
        <!-- 大会ロゴを表示 -->
        <img src="/static/logo.png" alt="Tournament Logo" style="max-width: 300px; height: auto;">
        <ul id="requestList">
            <!-- 既存のリクエストを表示 -->
            {{ requests_list }}
        </ul>
    </body>
    </html>
    '''.replace('{{ requests_list }}', ''.join([f"<li>{req['timestamp']} - {req['player_name']} (IP: {req['ip']})</li>" for req in replay_requests]))

if __name__ == '__main__':
    import eventlet
    socketio.run(app, debug=True)
