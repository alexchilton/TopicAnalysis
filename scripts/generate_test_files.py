"""Generate 3 monthly CSV files with realistic multilingual feedback for testing."""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent.parent / "demo_data"

# ---------------------------------------------------------------------------
# Feedback pools — real, natural-sounding text
# ---------------------------------------------------------------------------

POSITIVE = {
    "en": [
        "Absolutely love this app! The interface is so intuitive and responsive.",
        "Best customer experience I've had in years. The support team truly cares.",
        "This product has completely changed how I manage my daily workflow. Five stars!",
        "Shipping was lightning fast and the packaging was eco-friendly. Impressed!",
        "The latest update fixed every issue I had. Developers really listen to feedback.",
        "Great value for the price. I've recommended it to all my coworkers.",
        "The onboarding process was seamless. I was up and running in minutes.",
        "Really appreciate the attention to detail in the UI. Everything just works.",
        "Outstanding quality. I've been using it daily for three months without a single problem.",
        "Customer support responded within an hour and solved my issue on the first try.",
        "Exactly what I was looking for. Simple, elegant, and powerful.",
        "The free tier is generous enough for my needs. Might upgrade soon though!",
    ],
    "es": [
        "Me encanta esta aplicación, es muy fácil de usar y funciona de maravilla.",
        "El servicio al cliente fue excelente. Resolvieron mi problema en minutos.",
        "Producto de gran calidad. Superó todas mis expectativas.",
        "La actualización más reciente mejoró mucho el rendimiento. ¡Genial!",
        "Muy contento con mi compra. Lo recomiendo sin dudarlo.",
        "Interfaz intuitiva y bonita. Se nota que cuidan cada detalle.",
    ],
    "fr": [
        "Application fantastique ! L'interface est claire et agréable à utiliser.",
        "Le service client a été irréprochable. Problème résolu en un clin d'œil.",
        "Très satisfait de la qualité du produit. Je le recommande vivement.",
        "La mise à jour a vraiment amélioré les performances. Bravo à l'équipe !",
        "Rapport qualité-prix imbattable. Je suis client fidèle depuis un an.",
        "Livraison rapide et emballage soigné. Rien à redire.",
    ],
    "de": [
        "Bin absolut begeistert von der App. Läuft stabil und sieht super aus.",
        "Der Kundenservice hat mir innerhalb einer Stunde geholfen. Top!",
        "Hervorragende Qualität zum fairen Preis. Kann ich nur weiterempfehlen.",
        "Das letzte Update hat viele nützliche Funktionen gebracht. Sehr zufrieden!",
    ],
    "ja": [
        "このアプリは本当に使いやすくて、毎日愛用しています。おすすめです！",
        "カスタマーサポートの対応が素晴らしかったです。すぐに問題が解決しました。",
        "品質が非常に高く、価格以上の価値があります。大満足です。",
        "アップデートで動作がさらに快適になりました。開発チームに感謝します。",
    ],
}

NEGATIVE = {
    "en": [
        "The app crashes every time I try to export a report. Completely unusable.",
        "I've been waiting two weeks for a response from support. Unacceptable.",
        "After the latest update the battery drain is insane. Please fix this ASAP.",
        "The product arrived with a cracked screen and returning it has been a nightmare.",
        "Way too many ads. I'm paying for premium and still seeing banner ads everywhere.",
        "Terrible performance on Android. It takes 30 seconds just to load the dashboard.",
        "I was charged twice for my subscription and nobody seems to care.",
        "The search function is broken. It returns completely irrelevant results every time.",
        "Honestly disappointed. The features advertised on the website don't actually exist.",
        "Lost all my data after the migration. No warning, no backup option. Furious.",
        "The UI redesign is awful. Everything I need is now buried under three menus.",
        "Connection drops constantly. I can't rely on this for my business anymore.",
    ],
    "es": [
        "La aplicación se congela cada vez que intento subir un archivo. Muy frustrante.",
        "Llevo dos semanas esperando respuesta del soporte técnico. Inaceptable.",
        "Después de la última actualización, la batería se agota en pocas horas.",
        "El producto llegó defectuoso y el proceso de devolución es una pesadilla.",
        "Demasiados anuncios incluso en la versión de pago. No lo recomiendo.",
        "Perdí todos mis datos tras la migración. Estoy muy decepcionado.",
    ],
    "fr": [
        "L'application plante à chaque ouverture depuis la dernière mise à jour.",
        "Deux semaines sans réponse du support. C'est inadmissible.",
        "La qualité du produit est bien en dessous de ce qui était annoncé.",
        "Trop de publicités intrusives. J'ai payé pour la version premium, c'est scandaleux.",
        "J'ai perdu toutes mes données sans aucun avertissement. Très déçu.",
        "Le temps de chargement est insupportable. Plusieurs minutes pour ouvrir une page.",
    ],
    "de": [
        "Die App stürzt ständig ab, seit dem letzten Update. Sehr enttäuschend.",
        "Seit zwei Wochen keine Antwort vom Support. Das ist inakzeptabel.",
        "Viel zu viele Werbeanzeigen, selbst in der bezahlten Version. Nicht empfehlenswert.",
        "Das Produkt war bei Lieferung beschädigt und die Rückgabe ist kompliziert.",
    ],
    "ja": [
        "アプリが頻繁にクラッシュして仕事になりません。早急に修正してください。",
        "サポートに問い合わせて2週間経ちますが、まだ返答がありません。",
        "最新のアップデート後、バッテリーの消耗が激しくなりました。非常に困っています。",
        "広告が多すぎて使い物になりません。有料版でもこの状態は納得できません。",
    ],
}

NEUTRAL = {
    "en": [
        "The app works fine for basic tasks, but lacks some advanced features I need.",
        "Decent product overall. Nothing exceptional, but it gets the job done.",
        "I've been using it for a month now. It's okay but I'm still evaluating alternatives.",
        "The new design is different. Not sure if I prefer it over the old one yet.",
        "Delivery was on time. Product matches the description, nothing more nothing less.",
        "Works as expected. Would appreciate more customization options in future updates.",
        "It's a solid tool for beginners. Power users might find it a bit limited.",
        "Average experience. Some features are great, others need improvement.",
    ],
    "es": [
        "La aplicación funciona bien para lo básico, pero le faltan opciones avanzadas.",
        "Es un producto aceptable. Cumple su función, aunque no destaca en nada.",
        "Llevo un mes usándola. Está bien, pero todavía estoy evaluando otras opciones.",
        "El nuevo diseño es diferente. Aún no sé si me gusta más que el anterior.",
    ],
    "fr": [
        "L'application fonctionne correctement pour les tâches simples, sans plus.",
        "Produit correct dans l'ensemble. Rien d'exceptionnel, mais il fait le travail.",
        "Le nouveau design est différent. Je ne suis pas encore sûr de l'apprécier.",
        "Livraison dans les temps. Le produit correspond à la description, sans surprise.",
    ],
    "de": [
        "Die App funktioniert gut für grundlegende Aufgaben, aber es fehlen einige Funktionen.",
        "Ganz okay. Nichts Besonderes, aber es erfüllt seinen Zweck.",
        "Das neue Design ist gewöhnungsbedürftig. Bin noch unentschieden.",
    ],
    "ja": [
        "基本的な機能は問題なく使えますが、もう少し高度な機能が欲しいです。",
        "普通の製品です。特に不満はありませんが、特筆すべき点もありません。",
        "新しいデザインは慣れが必要です。前の方が良かったかもしれません。",
    ],
}

# ---------------------------------------------------------------------------
# Language distribution weights (approx 50% en, 15% es, 15% fr, 10% de, 10% ja)
# ---------------------------------------------------------------------------
LANGUAGES = ["en", "es", "fr", "de", "ja"]
LANG_WEIGHTS = [50, 15, 15, 10, 10]
LANG_LABELS = {"en": "English", "es": "Spanish", "fr": "French", "de": "German", "ja": "Japanese"}

# ---------------------------------------------------------------------------
# File configurations
# ---------------------------------------------------------------------------
FILES = [
    {
        "filename": "feedback_jan2024.csv",
        "year": 2024,
        "month": 1,
        "days": 31,
        "sources": ["app_store", "email", "survey"],
        "positive_pct": 60,
        "neutral_pct": 20,
        "negative_pct": 20,
        "count": 50,
    },
    {
        "filename": "feedback_feb2024.csv",
        "year": 2024,
        "month": 2,
        "days": 29,
        "sources": ["support_ticket", "chat", "twitter"],
        "positive_pct": 20,
        "neutral_pct": 25,
        "negative_pct": 55,
        "count": 50,
    },
    {
        "filename": "feedback_mar2024.csv",
        "year": 2024,
        "month": 3,
        "days": 31,
        "sources": ["web_form", "play_store", "email"],
        "positive_pct": 40,
        "neutral_pct": 30,
        "negative_pct": 30,
        "count": 50,
    },
]


def _pick_text(pool: dict[str, list[str]], lang: str) -> str:
    return random.choice(pool[lang])


def _random_timestamp(year: int, month: int, days: int) -> str:
    start = datetime(year, month, 1)
    offset = random.uniform(0, days * 24 * 3600 - 1)
    dt = start + timedelta(seconds=offset)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def generate_file(cfg: dict) -> Path:
    n_pos = round(cfg["count"] * cfg["positive_pct"] / 100)
    n_neg = round(cfg["count"] * cfg["negative_pct"] / 100)
    n_neu = cfg["count"] - n_pos - n_neg

    sentiments: list[str] = (
        ["positive"] * n_pos + ["negative"] * n_neg + ["neutral"] * n_neu
    )
    random.shuffle(sentiments)

    rows: list[dict[str, str]] = []
    for sentiment in sentiments:
        lang = random.choices(LANGUAGES, weights=LANG_WEIGHTS, k=1)[0]
        pool = {"positive": POSITIVE, "negative": NEGATIVE, "neutral": NEUTRAL}[sentiment]
        text = _pick_text(pool, lang)
        rows.append(
            {
                "text": text,
                "source": random.choice(cfg["sources"]),
                "timestamp": _random_timestamp(cfg["year"], cfg["month"], cfg["days"]),
                "language": LANG_LABELS[lang],
            }
        )

    rows.sort(key=lambda r: r["timestamp"])

    filepath = DEMO_DIR / cfg["filename"]
    with filepath.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "source", "timestamp", "language"])
        writer.writeheader()
        writer.writerows(rows)

    return filepath


def main() -> None:
    random.seed(42)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    for cfg in FILES:
        path = generate_file(cfg)
        print(f"✓ Generated {path}  ({cfg['count']} rows)")


if __name__ == "__main__":
    main()
