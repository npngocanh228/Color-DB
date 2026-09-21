#!/usr/bin/env python3
"""
=============================================================================
GIAO DIỆN MINI APP BẮN PUSH NOTIFICATION BACKEND (WEB DASHBOARD)
Khởi động: python3 tools/noti_admin_server.py
Truy cập: http://localhost:8080
=============================================================================
"""

import os
import sys
import json
import socket
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
sys.path.append(TOOLS_DIR)

try:
    import push_notification_tool as pnt
except ImportError:
    pnt = None

HTML_PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trung Tâm Bắn Thông Báo - Pixel Art</title>
    <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
    <style>
        .phone-bezel {
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4), 0 0 0 12px #1f2937, 0 0 0 14px #374151;
        }
        .notch {
            width: 120px;
            height: 24px;
            background: #1f2937;
            border-bottom-left-radius: 12px;
            border-bottom-right-radius: 12px;
        }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased">
    <!-- Header -->
    <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-pink-500 flex items-center justify-center text-xl shadow-lg shadow-indigo-500/20">
                    🎨
                </div>
                <div>
                    <h1 class="text-lg font-bold text-white tracking-tight">Pixel Art - Push Notification Admin</h1>
                    <p class="text-xs text-slate-400">Giao diện điều khiển gửi thông báo đa ngôn ngữ Firebase Cloud Messaging</p>
                </div>
            </div>
            <div id="statusBadge" class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Hệ Thống Sẵn Sàng
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        <!-- Left Column: Bảng Điều Khiển (Form) -->
        <div class="lg:col-span-7 space-y-6">
            <div class="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
                <h2 class="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
                    <span class="text-indigo-400">⚙️</span> 1. Cấu Hình Đối Tượng Nhận Thông Báo
                </h2>

                <!-- 1. Chọn hình thức gửi -->
                <div>
                    <label class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Hình thức gửi (Target)</label>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        <label class="cursor-pointer border border-slate-700 bg-slate-800/50 p-3 rounded-xl flex flex-col items-center text-center hover:border-indigo-500 transition-all target-option has-[:checked]:border-indigo-500 has-[:checked]:bg-indigo-500/10">
                            <input type="radio" name="target_mode" value="token" checked class="hidden" onchange="updateTargetUI()">
                            <span class="text-xl mb-1">🎯</span>
                            <span class="text-xs font-medium">1 FCM Token</span>
                        </label>
                        <label class="cursor-pointer border border-slate-700 bg-slate-800/50 p-3 rounded-xl flex flex-col items-center text-center hover:border-indigo-500 transition-all target-option has-[:checked]:border-indigo-500 has-[:checked]:bg-indigo-500/10">
                            <input type="radio" name="target_mode" value="user_id" class="hidden" onchange="updateTargetUI()">
                            <span class="text-xl mb-1">👤</span>
                            <span class="text-xs font-medium">1 User ID</span>
                        </label>
                        <label class="cursor-pointer border border-slate-700 bg-slate-800/50 p-3 rounded-xl flex flex-col items-center text-center hover:border-indigo-500 transition-all target-option has-[:checked]:border-indigo-500 has-[:checked]:bg-indigo-500/10">
                            <input type="radio" name="target_mode" value="topic_lang" class="hidden" onchange="updateTargetUI()">
                            <span class="text-xl mb-1">📢</span>
                            <span class="text-xs font-medium">Topic Ngôn Ngữ</span>
                        </label>
                        <label class="cursor-pointer border border-slate-700 bg-slate-800/50 p-3 rounded-xl flex flex-col items-center text-center hover:border-indigo-500 transition-all target-option has-[:checked]:border-indigo-500 has-[:checked]:bg-indigo-500/10">
                            <input type="radio" name="target_mode" value="all_firestore" class="hidden" onchange="updateTargetUI()">
                            <span class="text-xl mb-1">👥</span>
                            <span class="text-xs font-medium">Tất Cả Users</span>
                        </label>
                    </div>
                </div>

                <!-- Input Token / User ID -->
                <div id="targetInputContainer">
                    <label id="targetInputLabel" class="block text-xs font-semibold text-slate-300 mb-1.5">FCM Token của thiết bị</label>
                    <input type="text" id="targetValue" placeholder="Nhập chuỗi FCM Registration Token..." class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all">
                </div>

                <!-- 2. Chọn ngôn ngữ & Mẫu thông báo -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1.5">Ngôn ngữ hiển thị (Language)</label>
                        <select id="langSelect" onchange="onTemplateOrLangChange()" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-indigo-500">
                            <option value="vi" selected>🇻🇳 Tiếng Việt (vi)</option>
                            <option value="en">🇺🇸 English (en)</option>
                            <option value="ja">🇯🇵 日本語 (ja)</option>
                            <option value="ko">🇰🇷 한국어 (ko)</option>
                            <option value="zh">🇨🇳 中文 (zh)</option>
                            <option value="es">🇪🇸 Español (es)</option>
                            <option value="pt">🇧🇷 Português (pt)</option>
                            <option value="fr">🇫🇷 Français (fr)</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1.5">Mẫu thông báo (Template Preset)</label>
                        <select id="templateSelect" onchange="onTemplateOrLangChange()" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-indigo-500">
                            <option value="new_artworks">🎨 Có 10+ tranh mới hôm nay</option>
                            <option value="unfinished_reminder">⏳ Nhắc nhở hoàn thành tranh dở dang</option>
                            <option value="daily_streak">🔥 Giữ chuỗi ngày tô màu</option>
                            <option value="weekend_special">✨ Sự kiện thư giãn cuối tuần</option>
                            <option value="custom">✍️ Tự nhập nội dung tùy chỉnh</option>
                        </select>
                    </div>
                </div>

                <!-- 3. Tiêu đề & Nội dung -->
                <div class="space-y-3 pt-2">
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1.5">Tiêu đề thông báo (Title)</label>
                        <input type="text" id="titleInput" oninput="updateLivePreview()" placeholder="Tiêu đề thông báo..." class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500">
                    </div>

                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1.5">Nội dung thông báo (Body)</label>
                        <textarea id="bodyInput" rows="3" oninput="updateLivePreview()" placeholder="Nội dung thông báo..." class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"></textarea>
                    </div>

                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1.5">Mã tranh mở thẳng khi click (Artwork ID Deep Link - Tùy chọn)</label>
                        <input type="text" id="artworkIdInput" placeholder="Ví dụ: CBN_Dragon_30x30px hoặc để trống..." class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500">
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="pt-4 flex flex-col sm:flex-row gap-3">
                    <button id="btnSendReal" onclick="sendNotification(false)" class="flex-1 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold py-3 px-6 rounded-xl shadow-lg shadow-indigo-500/25 active:scale-[0.98] transition-all flex items-center justify-center gap-2">
                        <span>🚀 Bắn Thông Báo Ngay</span>
                    </button>
                    <button id="btnSendDry" onclick="sendNotification(true)" class="bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold py-3 px-5 rounded-xl border border-slate-700 active:scale-[0.98] transition-all flex items-center justify-center gap-2">
                        <span>🧪 Thử Nghiệm (Dry Run)</span>
                    </button>
                </div>
            </div>

            <!-- Console Log Box -->
            <div class="bg-slate-950 border border-slate-800 rounded-2xl p-4 font-mono text-xs space-y-2">
                <div class="flex items-center justify-between text-slate-400 border-b border-slate-800 pb-2">
                    <span class="flex items-center gap-1.5">
                        <span class="w-2.5 h-2.5 rounded-full bg-amber-400/80"></span>
                        Nhật Ký Gửi (Output Log)
                    </span>
                    <button onclick="clearLog()" class="hover:text-white transition-colors">Xóa</button>
                </div>
                <div id="logContent" class="text-slate-300 min-h-[90px] max-h-[160px] overflow-y-auto space-y-1">
                    <div class="text-slate-500 italic">Sẵn sàng gửi thông báo... Hãy chọn tùy chọn và bấm nút trên.</div>
                </div>
            </div>
        </div>

        <!-- Right Column: Live Phone Mockup Preview -->
        <div class="lg:col-span-5 flex flex-col items-center">
            <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <span>📱</span> Xem Trước Trên Màn Hình Khóa Điện Thoại
            </div>

            <div class="phone-bezel w-[340px] h-[640px] bg-slate-900 rounded-[48px] p-4 relative overflow-hidden flex flex-col select-none border border-slate-700">
                <!-- Notch -->
                <div class="absolute top-0 left-1/2 -translate-x-1/2 notch flex items-center justify-center">
                    <div class="w-3 h-3 rounded-full bg-slate-800 mr-2"></div>
                    <div class="w-2 h-2 rounded-full bg-slate-700"></div>
                </div>

                <!-- Status Bar -->
                <div class="pt-2 px-4 flex justify-between items-center text-xs font-semibold text-slate-300">
                    <span id="phoneClock">20:15</span>
                    <div class="flex items-center gap-1.5 text-xs">
                        <span>5G</span>
                        <span>100%</span>
                    </div>
                </div>

                <!-- Lockscreen Clock -->
                <div class="mt-12 text-center">
                    <div id="phoneBigClock" class="text-6xl font-light tracking-tight text-white">20:15</div>
                    <div id="phoneDate" class="text-xs font-medium text-slate-400 mt-1">Thứ Hai, 21 tháng 9</div>
                </div>

                <!-- Push Notification Banner Card -->
                <div class="mt-8 mx-1 bg-slate-800/90 backdrop-blur-md border border-slate-700/80 rounded-2xl p-3.5 shadow-2xl transition-all duration-300 hover:scale-[1.02]">
                    <!-- Header of Noti -->
                    <div class="flex items-center justify-between mb-1.5">
                        <div class="flex items-center gap-2">
                            <div class="w-5 h-5 rounded-md bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center text-xs text-white font-bold">
                                🎨
                            </div>
                            <span class="text-[11px] font-bold text-slate-200 uppercase tracking-wider">Pixel Art Paint</span>
                        </div>
                        <span class="text-[10px] text-slate-400">Vừa xong</span>
                    </div>

                    <!-- Noti Content -->
                    <div class="text-xs font-bold text-white mb-0.5" id="previewTitle">
                        🎨 Có 10+ tranh mới hôm nay!
                    </div>
                    <div class="text-[11px] text-slate-300 leading-snug" id="previewBody">
                        Nhiều chủ đề cực đẹp vừa được cập nhật. Vào tô màu thư giãn ngay nhé!
                    </div>
                </div>

                <!-- Hint footer -->
                <div class="mt-auto pb-4 text-center">
                    <div class="w-32 h-1 bg-slate-600 rounded-full mx-auto mb-2"></div>
                    <span class="text-[10px] text-slate-500">Chạm vào thông báo để mở thẳng vào bức tranh</span>
                </div>
            </div>
        </div>

    </main>

    <script>
        // Templates dictionary
        const TEMPLATES = """ + json.dumps(getattr(pnt, "TEMPLATES", {}), ensure_ascii=False) + """;

        function updateTargetUI() {
            const mode = document.querySelector('input[name="target_mode"]:checked').value;
            const container = document.getElementById('targetInputContainer');
            const label = document.getElementById('targetInputLabel');
            const input = document.getElementById('targetValue');

            if (mode === 'token') {
                container.style.display = 'block';
                label.innerText = 'FCM Registration Token của thiết bị';
                input.placeholder = 'Nhập chuỗi fcmToken của người dùng...';
            } else if (mode === 'user_id') {
                container.style.display = 'block';
                label.innerText = 'User ID (UID) trong Firestore';
                input.placeholder = 'Nhập UID của người dùng trong Firestore...';
            } else if (mode === 'topic_lang') {
                container.style.display = 'none';
            } else if (mode === 'all_firestore') {
                container.style.display = 'none';
            }
        }

        function onTemplateOrLangChange() {
            const template = document.getElementById('templateSelect').value;
            const lang = document.getElementById('langSelect').value;

            if (template === 'custom') {
                document.getElementById('titleInput').value = '';
                document.getElementById('bodyInput').value = '';
                updateLivePreview();
                return;
            }

            if (TEMPLATES[template] && TEMPLATES[template][lang]) {
                const item = TEMPLATES[template][lang];
                document.getElementById('titleInput').value = item.title;
                document.getElementById('bodyInput').value = item.body;
            } else if (TEMPLATES[template] && TEMPLATES[template]['en']) {
                const item = TEMPLATES[template]['en'];
                document.getElementById('titleInput').value = item.title;
                document.getElementById('bodyInput').value = item.body;
            }

            updateLivePreview();
        }

        function updateLivePreview() {
            const title = document.getElementById('titleInput').value || 'Tiêu đề thông báo...';
            const body = document.getElementById('bodyInput').value || 'Nội dung thông báo hiển thị tại đây...';

            document.getElementById('previewTitle').innerText = title;
            document.getElementById('previewBody').innerText = body;
        }

        function appendLog(text, type = 'info') {
            const logBox = document.getElementById('logContent');
            const item = document.createElement('div');
            const time = new Date().toLocaleTimeString();
            if (type === 'success') {
                item.className = 'text-emerald-400 font-semibold';
            } else if (type === 'error') {
                item.className = 'text-rose-400 font-semibold';
            } else {
                item.className = 'text-slate-300';
            }
            item.innerText = `[${time}] ${text}`;
            logBox.appendChild(item);
            logBox.scrollTop = logBox.scrollHeight;
        }

        function clearLog() {
            document.getElementById('logContent').innerHTML = '';
        }

        async function sendNotification(dryRun) {
            const mode = document.querySelector('input[name="target_mode"]:checked').value;
            const targetVal = document.getElementById('targetValue').value.trim();
            const lang = document.getElementById('langSelect').value;
            const template = document.getElementById('templateSelect').value;
            const title = document.getElementById('titleInput').value.trim();
            const body = document.getElementById('bodyInput').value.trim();
            const artworkId = document.getElementById('artworkIdInput').value.trim();

            if (mode === 'token' && !targetVal) {
                alert('Vui lòng nhập FCM Token của thiết bị!');
                return;
            }
            if (mode === 'user_id' && !targetVal) {
                alert('Vui lòng nhập User ID trong Firestore!');
                return;
            }

            appendLog(`Đang gửi yêu cầu (dry_run=${dryRun}, mode=${mode}, lang=${lang})...`);

            const payload = {
                target_mode: mode,
                target_value: targetVal,
                lang: lang,
                template: template,
                title: title,
                body: body,
                artwork_id: artworkId,
                dry_run: dryRun
            };

            try {
                const res = await fetch('/api/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    appendLog(`✓ Thành công: ${data.message}`, 'success');
                    if (data.detail) appendLog(data.detail);
                } else {
                    appendLog(`✗ Lỗi: ${data.message}`, 'error');
                }
            } catch (err) {
                appendLog(`✗ Lỗi kết nối tới Server: ${err}`, 'error');
            }
        }

        // Clock initialization
        function updateClock() {
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const timeStr = `${hours}:${minutes}`;
            document.getElementById('phoneClock').innerText = timeStr;
            document.getElementById('phoneBigClock').innerText = timeStr;
        }
        setInterval(updateClock, 1000);
        updateClock();

        // Initial trigger
        onTemplateOrLangChange();
        updateTargetUI();
    </script>
</body>
</html>
"""


class AdminRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif parsed.path == "/api/status":
            has_key = os.path.exists(os.path.join(TOOLS_DIR, "serviceAccountKey.json"))
            self.send_json({"has_credentials": has_key})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/send":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                data = json.loads(body)
            except Exception as e:
                self.send_json({"success": False, "message": f"Invalid JSON: {e}"})
                return

            res = self.handle_send(data)
            self.send_json(res)
        else:
            self.send_response(404)
            self.end_headers()

    def send_json(self, obj):
        out = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(out)

    def handle_send(self, req):
        mode = req.get("target_mode")
        target_val = req.get("target_value", "")
        lang = req.get("lang", "en")
        template = req.get("template", "new_artworks")
        title = req.get("title")
        body = req.get("body")
        artwork_id = req.get("artwork_id")
        dry_run = req.get("dry_run", False)

        extra_data = {}
        if artwork_id:
            extra_data["artworkId"] = artwork_id

        # Kiểm tra Credentials nếu không phải dry_run
        cred_path = os.path.join(TOOLS_DIR, "serviceAccountKey.json")
        has_cred = os.path.exists(cred_path)

        if not dry_run and not has_cred:
            return {
                "success": False,
                "message": "Chưa có file serviceAccountKey.json! Vui lòng tải từ Firebase Console và đặt vào coloring-data/tools/, hoặc bấm nút 'Thử Nghiệm (Dry Run)'."
            }

        # Nếu dry_run hoặc có credentials
        if dry_run or not pnt:
            return {
                "success": True,
                "message": f"[DRY-RUN THÀNH CÔNG] Đã mô phỏng gửi thành công cho mode={mode}, lang={lang}.",
                "detail": f"Tiêu đề: '{title}' | Nội dung: '{body}' | Target: '{target_val or mode}'"
            }

        try:
            pnt.init_firebase(cred_path)
            if mode == "token":
                ok = pnt.send_to_token(target_val, title, body, extra_data, dry_run=False)
                return {"success": ok, "message": f"Gửi tới Token {target_val[:12]}... thành công!" if ok else "Gửi thất bại."}
            elif mode == "user_id":
                pnt.push_by_user_id(target_val, template, title, body, extra_data, dry_run=False)
                return {"success": True, "message": f"Đã gửi thành công tới User '{target_val}'!"}
            elif mode == "topic_lang":
                topic_name = f"lang_{lang}"
                ok = pnt.send_to_topic(topic_name, title, body, extra_data, dry_run=False)
                return {"success": ok, "message": f"Đã gửi thành công tới Topic '{topic_name}'!"}
            elif mode == "all_firestore":
                pnt.push_all_firestore_users(template, title, body, extra_data, dry_run=False)
                return {"success": True, "message": "Đã hoàn tất quét và gửi tới toàn bộ Users trong Firestore!"}
            else:
                return {"success": False, "message": f"Mode '{mode}' không hợp lệ."}
        except Exception as e:
            return {"success": False, "message": f"Lỗi xử lý Firebase: {e}"}


def find_free_port(start_port=8080):
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) != 0:
                return port
        port += 1
    return 8080


def main():
    port = find_free_port(8080)
    server_address = ("", port)
    httpd = HTTPServer(server_address, AdminRequestHandler)

    url = f"http://localhost:{port}"
    print(f"\n=======================================================")
    print(f"🚀 GIAO DIỆN BẮN THÔNG BÁO PUSH NOTIFICATION ĐÃ KHỞI CHẠY!")
    print(f"👉 Mở trình duyệt tại: {url}")
    print(f"=======================================================\n")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Đã tắt Web Server.")
        httpd.server_close()


if __name__ == "__main__":
    main()
