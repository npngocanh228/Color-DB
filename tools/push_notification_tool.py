#!/usr/bin/env python3
"""
=============================================================================
TOOL PUSH NOTIFICATION BACKEND CHO FIREBASE CLOUD MESSAGING (FCM)
Hỗ trợ:
- Gửi đích danh từng user / FCM Token theo đúng ngôn ngữ app của họ
- Tự động lấy Token & Ngôn ngữ từ Firestore
- Bắn hàng loạt theo Topic ngôn ngữ (lang_vi, lang_en, lang_ja...)
- Thư viện mẫu thông báo đa ngôn ngữ sẵn có (New Artworks, Streak, Reminder...)
=============================================================================
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional, List

# Các mẫu thông báo đa ngôn ngữ soạn sẵn cho game tô màu
TEMPLATES = {
    "new_artworks": {
        "vi": {
            "title": "🎨 Có 10+ tranh mới hôm nay!",
            "body": "Nhiều chủ đề cực đẹp vừa được cập nhật. Vào tô màu thư giãn ngay nhé!"
        },
        "en": {
            "title": "🎨 10+ New Artworks Available!",
            "body": "Fresh and beautiful pixel pages just dropped. Relax and color now!"
        },
        "ja": {
            "title": "🎨 今日の新しいイラストが登場！",
            "body": "新しいぬりえが追加されました。今すぐリラックスして塗ってみよう！"
        },
        "ko": {
            "title": "🎨 오늘 새로운 그림 10+개 추가!",
            "body": "새로운 컬러링 페이지가 업데이트되었습니다. 지금 색칠하며 힐링하세요!"
        },
        "zh": {
            "title": "🎨 今日新增 10+ 幅新画作！",
            "body": "超多精美像素画作已更新，快来轻松填色吧！"
        },
        "es": {
            "title": "🎨 ¡Más de 10 nuevos dibujos hoy!",
            "body": "Nuevas páginas de pixel art listas. ¡Relájate y colorea ahora!"
        },
        "pt": {
            "title": "🎨 Mais de 10 novos desenhos hoje!",
            "body": "Novas páginas incríveis acabaram de chegar. Relaxe e pinte agora!"
        },
        "fr": {
            "title": "🎨 10+ nouveaux coloriages aujourd'hui !",
            "body": "De magnifiques pages pixel art viennent d'arriver. Détendez-vous et coloriez !"
        }
    },
    "unfinished_reminder": {
        "vi": {
            "title": "⏳ Bức tranh của bạn sắp xong rồi!",
            "body": "Tác phẩm đang chờ bạn hoàn thiện nốt. Vào tô nốt các nét cuối nhé!"
        },
        "en": {
            "title": "⏳ Your artwork is almost done!",
            "body": "Your masterpiece is waiting for you. Tap to finish it today!"
        },
        "ja": {
            "title": "⏳ イラストがもうすぐ完成します！",
            "body": "あなたの作品が待っています。最後の仕上げをしましょう！"
        },
        "ko": {
            "title": "⏳ 그림이 거의 다 완성되었습니다!",
            "body": "작품이 기다리고 있습니다. 지금 마지막 색칠을 완성해보세요!"
        },
        "zh": {
            "title": "⏳ 你的画作快要完成啦！",
            "body": "精美大作正在等你，快来完成最后的涂色吧！"
        },
        "es": {
            "title": "⏳ ¡Tu dibujo está casi listo!",
            "body": "Tu obra de arte te espera. ¡Entra y dale los toques finales!"
        },
        "pt": {
            "title": "⏳ Seu desenho está quase pronto!",
            "body": "Sua obra-prima está esperando. Venha dar os toques finais!"
        },
        "fr": {
            "title": "⏳ Votre coloriage est presque terminé !",
            "body": "Votre chef-d'œuvre vous attend. Entrez pour y mettre la touche finale !"
        }
    },
    "daily_streak": {
        "vi": {
            "title": "🔥 Giữ vững chuỗi ngày tô màu!",
            "body": "Chỉ còn vài giờ để hoàn thành thử thách hôm nay và nhận phần thưởng sao."
        },
        "en": {
            "title": "🔥 Keep your coloring streak alive!",
            "body": "Only a few hours left to complete today's art and claim your bonus stars."
        },
        "ja": {
            "title": "🔥 連続記録をキープしよう！",
            "body": "今日のデイリーアートを完成させて、ボーナススターを獲得しましょう。"
        },
        "ko": {
            "title": "🔥 연속 색칠 스트릭을 이어가세요!",
            "body": "오늘의 미션을 완료하고 보너스 별을 획득할 시간이 얼마 남지 않았습니다."
        },
        "zh": {
            "title": "🔥 保持你的连续涂色记录！",
            "body": "今日挑战即将截止，快来完成画作领取星星奖励吧！"
        },
        "es": {
            "title": "🔥 ¡Mantén tu racha de arte!",
            "body": "Quedan pocas horas para completar el reto diario y ganar estrellas extra."
        },
        "pt": {
            "title": "🔥 Mantenha sua sequência diária!",
            "body": "Faltam poucas horas para completar a arte de hoje e ganhar estrelas bônus."
        },
        "fr": {
            "title": "🔥 Gardez votre série quotidienne active !",
            "body": "Il ne reste que quelques heures pour compléter le dessin du jour et gagner vos étoiles."
        }
    },
    "weekend_special": {
        "vi": {
            "title": "✨ Cuối tuần thư giãn cùng Pixel Art",
            "body": "Bộ sưu tập tranh phong cảnh và anime đặc biệt đã mở khóa miễn phí hôm nay!"
        },
        "en": {
            "title": "✨ Weekend Chill with Pixel Art",
            "body": "Special weekend collection is unlocked for free today. Have fun!"
        },
        "ja": {
            "title": "✨ 週末のひとときをぬりえでリラックス",
            "body": "今週末限定の特別イラストコレクションが無料開放中！"
        },
        "ko": {
            "title": "✨ 픽셀 아트로 즐기는 주말 힐링",
            "body": "주말 특별 컬렉션이 오늘 무료로 열렸습니다. 지금 즐겨보세요!"
        },
        "zh": {
            "title": "✨ 周末轻松时刻，一起来像素涂色",
            "body": "周末特别画作集今日限时免费解锁，快来体验吧！"
        },
        "es": {
            "title": "✨ Fin de semana de relax con Pixel Art",
            "body": "Colección especial de fin de semana desbloqueada gratis hoy. ¡Disfrútala!"
        },
        "pt": {
            "title": "✨ Fim de semana relax com Pixel Art",
            "body": "Coleção especial de fim de semana liberada grátis hoje. Aproveite!"
        },
        "fr": {
            "title": "✨ Détente de week-end avec Pixel Art",
            "body": "Une collection spéciale week-end est débloquée gratuitement aujourd'hui !"
        }
    }
}


def get_localized_message(template_name: str, lang: str, custom_title: Optional[str] = None, custom_body: Optional[str] = None) -> tuple:
    """Lấy tiêu đề và nội dung theo ngôn ngữ"""
    lang = lang.lower().split("-")[0].split("_")[0]

    if custom_title and custom_body:
        return custom_title, custom_body

    if template_name in TEMPLATES:
        tpl_group = TEMPLATES[template_name]
        msg = tpl_group.get(lang) or tpl_group.get("en")
        title = custom_title or msg["title"]
        body = custom_body or msg["body"]
        return title, body

    return "Pixel Art Coloring", "New art is ready for you!"


def init_firebase(cred_path: Optional[str] = None):
    """Khởi tạo Firebase Admin SDK"""
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError:
        print("[!] Chưa cài đặt thư viện firebase-admin.")
        print("[*] Vui lòng chạy lệnh: pip3 install firebase-admin")
        sys.exit(1)

    if not firebase_admin._apps:
        if not cred_path:
            # Tìm file serviceAccountKey.json tự động
            possible_paths = [
                os.path.join(os.getcwd(), "serviceAccountKey.json"),
                os.path.join(os.path.dirname(__file__), "serviceAccountKey.json"),
                os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
            ]
            for p in possible_paths:
                if p and os.path.exists(p):
                    cred_path = p
                    break

        if not cred_path or not os.path.exists(cred_path):
            print("[!] LỖI: Không tìm thấy file 'serviceAccountKey.json'.")
            print("[*] Hướng dẫn: Tải file từ Firebase Console -> Project settings -> Service accounts")
            print("[*] Sau đó lưu vào thư mục này hoặc truyền qua cờ: --cred path/to/serviceAccountKey.json")
            sys.exit(1)

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print(f"[+] Đã kết nối Firebase với credentials: {cred_path}")


def send_to_token(token: str, title: str, body: str, data: Optional[Dict[str, str]] = None, dry_run: bool = False) -> bool:
    """Gửi thông báo tới 1 FCM Token"""
    if dry_run:
        print(f"[DRY-RUN] Gửi tới Token: {token[:15]}... | Tiêu đề: '{title}' | Nội dung: '{body}'")
        return True

    from firebase_admin import messaging

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        data=data or {},
        token=token
    )

    try:
        response = messaging.send(message)
        print(f"[✓] Đã gửi thành công! Message ID: {response}")
        return True
    except Exception as e:
        print(f"[✗] Gửi thất bại tới {token[:15]}...: {e}")
        return False


def send_to_topic(topic: str, title: str, body: str, data: Optional[Dict[str, str]] = None, dry_run: bool = False) -> bool:
    """Gửi thông báo tới 1 Topic"""
    if dry_run:
        print(f"[DRY-RUN] Gửi tới Topic: '{topic}' | Tiêu đề: '{title}' | Nội dung: '{body}'")
        return True

    from firebase_admin import messaging

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        data=data or {},
        topic=topic
    )

    try:
        response = messaging.send(message)
        print(f"[✓] Đã gửi Topic '{topic}' thành công! Message ID: {response}")
        return True
    except Exception as e:
        print(f"[✗] Gửi Topic '{topic}' thất bại: {e}")
        return False


def push_by_user_id(user_id: str, template: str, custom_title: Optional[str] = None, custom_body: Optional[str] = None, extra_data: Optional[Dict[str, str]] = None, dry_run: bool = False):
    """Lấy Token & Ngôn ngữ của User từ Firestore rồi gửi"""
    from firebase_admin import firestore
    db = firestore.client()

    doc = db.collection("users").document(user_id).get()
    if not doc.exists:
        print(f"[!] Không tìm thấy User ID '{user_id}' trong Firestore!")
        return

    data = doc.to_dict() or {}
    token = data.get("fcmToken")
    lang = data.get("language", "en")

    if not token:
        print(f"[!] User '{user_id}' chưa có fcmToken trong Firestore!")
        return

    title, body = get_localized_message(template, lang, custom_title, custom_body)
    print(f"[*] User: {user_id} | Ngôn ngữ: {lang} | Token: {token[:15]}...")
    send_to_token(token, title, body, extra_data, dry_run)


def push_all_firestore_users(template: str, custom_title: Optional[str] = None, custom_body: Optional[str] = None, extra_data: Optional[Dict[str, str]] = None, dry_run: bool = False):
    """Quét toàn bộ users trong Firestore và gửi đúng ngôn ngữ của từng người"""
    from firebase_admin import firestore
    db = firestore.client()

    print("[*] Đang đọc danh sách users từ Firestore...")
    users_ref = db.collection("users").stream()

    total = 0
    success = 0
    for doc in users_ref:
        u_data = doc.to_dict()
        token = u_data.get("fcmToken")
        lang = u_data.get("language", "en")

        if token:
            total += 1
            title, body = get_localized_message(template, lang, custom_title, custom_body)
            if send_to_token(token, title, body, extra_data, dry_run):
                success += 1

    print(f"\n[=== HOÀN TẤT GỬI NOTIFICATION ===]")
    print(f"- Tổng số user có Token: {total}")
    print(f"- Thành công: {success}")


def push_all_topics_by_language(template: str, custom_title: Optional[str] = None, custom_body: Optional[str] = None, extra_data: Optional[Dict[str, str]] = None, dry_run: bool = False):
    """Bắn thông báo vào từng topic ngôn ngữ (lang_vi, lang_en, lang_ja...)"""
    languages = ["vi", "en", "ja", "ko", "zh", "es", "pt", "fr"]
    print(f"[*] Bắt đầu gửi vào {len(languages)} topics ngôn ngữ...")

    for lang in languages:
        topic_name = f"lang_{lang}"
        title, body = get_localized_message(template, lang, custom_title, custom_body)
        send_to_topic(topic_name, title, body, extra_data, dry_run)


def main():
    parser = argparse.ArgumentParser(description="Tool Backend Push Notification đa ngôn ngữ qua Firebase Cloud Messaging (FCM)")

    # Target
    parser.add_argument("--token", type=str, help="FCM Token của thiết bị muốn gửi trực tiếp")
    parser.add_argument("--lang", type=str, default="en", help="Ngôn ngữ khi gửi bằng --token (vd: vi, en, ja, ko, zh)")
    parser.add_argument("--user-id", type=str, help="User ID trong Firestore (tự động lấy token và language của user)")
    parser.add_argument("--from-firestore", action="store_true", help="Gửi cho toàn bộ users trong Firestore theo đúng ngôn ngữ của từng người")
    parser.add_argument("--topic-lang", action="store_true", help="Gửi vào các Topic ngôn ngữ (lang_vi, lang_en, lang_ja...)")

    # Nội dung
    parser.add_argument("--template", choices=list(TEMPLATES.keys()), default="new_artworks",
                        help=f"Mẫu thông báo có sẵn: {list(TEMPLATES.keys())}")
    parser.add_argument("--title", type=str, help="Tiêu đề tùy chỉnh (ghi đè template)")
    parser.add_argument("--body", type=str, help="Nội dung tùy chỉnh (ghi đè template)")
    parser.add_argument("--data", type=str, help="Dữ liệu JSON kèm theo (vd: '{\"artworkId\":\"CBN_Dragon\"}')")

    # Cấu hình
    parser.add_argument("--cred", type=str, help="Đường dẫn tới file serviceAccountKey.json của Firebase")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử nghiệm in ra nội dung, không gửi thật")

    args = parser.parse_args()

    extra_data = {}
    if args.data:
        try:
            extra_data = json.loads(args.data)
        except Exception:
            print("[!] Format --data JSON không hợp lệ!")

    if not args.dry_run:
        init_firebase(args.cred)

    # 1. Gửi trực tiếp theo Token
    if args.token:
        title, body = get_localized_message(args.template, args.lang, args.title, args.body)
        print(f"[*] Gửi tới Token đơn vị: lang={args.lang}")
        send_to_token(args.token, title, body, extra_data, args.dry_run)

    # 2. Gửi theo User ID (Firestore)
    elif args.user_id:
        push_by_user_id(args.user_id, args.template, args.title, args.body, extra_data, args.dry_run)

    # 3. Gửi toàn bộ Users trong Firestore
    elif args.from_firestore:
        push_all_firestore_users(args.template, args.title, args.body, extra_data, args.dry_run)

    # 4. Gửi vào các Topics ngôn ngữ
    elif args.topic_lang:
        push_all_topics_by_language(args.template, args.title, args.body, extra_data, args.dry_run)

    else:
        print("[!] Bạn cần chỉ định ít nhất 1 phương thức gửi: --token, --user-id, --from-firestore, hoặc --topic-lang")
        print("[*] Xem hướng dẫn chi tiết: python3 push_notification_tool.py --help")


if __name__ == "__main__":
    main()
