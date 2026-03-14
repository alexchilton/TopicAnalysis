"""Generate synthetic multi-language demo data."""

from __future__ import annotations

import csv
import io
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

FEEDBACK_TEMPLATES = {
    "en": {
        "positive": [
            "Absolutely love this product! Best purchase I've made.",
            "Customer service was incredibly helpful and resolved my issue quickly.",
            "Great quality, fast shipping. Will definitely order again.",
            "The new feature update is amazing, exactly what I needed.",
            "Very satisfied with the experience. Highly recommend!",
            "Excellent value for money. Exceeded my expectations.",
            "The team went above and beyond to help me. Outstanding!",
            "Really impressed with the build quality and design.",
        ],
        "negative": [
            "Product arrived damaged and customer support was unhelpful.",
            "Terrible experience. Waited 3 weeks for delivery that never came.",
            "The software crashes constantly. Very frustrating.",
            "Poor quality materials. Broke after two weeks of use.",
            "Worst customer service I've ever encountered.",
            "Not worth the price. Very disappointing quality.",
            "The app is full of bugs. Each update makes it worse.",
            "Misleading product description. Nothing like advertised.",
        ],
        "neutral": [
            "Product works as described. Nothing special.",
            "Average experience. Delivery was on time.",
            "It's okay for the price point. Nothing to complain about.",
            "Standard service, met expectations but didn't exceed them.",
            "Functional product. Does what it says.",
        ],
    },
    "es": {
        "positive": [
            "¡Me encanta este producto! La mejor compra que he hecho.",
            "El servicio al cliente fue increíblemente útil.",
            "Excelente calidad, envío rápido. Definitivamente pediré de nuevo.",
            "Muy satisfecho con la experiencia. ¡Lo recomiendo!",
        ],
        "negative": [
            "El producto llegó dañado y el soporte no ayudó.",
            "Experiencia terrible. Esperé 3 semanas sin resultado.",
            "Mala calidad. Se rompió después de dos semanas.",
            "El peor servicio al cliente que he experimentado.",
        ],
        "neutral": [
            "El producto funciona como se describe. Nada especial.",
            "Experiencia promedio. La entrega fue puntual.",
        ],
    },
    "fr": {
        "positive": [
            "J'adore ce produit ! Le meilleur achat que j'ai fait.",
            "Le service client était incroyablement utile et efficace.",
            "Excellente qualité, livraison rapide. Je recommande vivement !",
            "Très satisfait de l'expérience. Hautement recommandé !",
        ],
        "negative": [
            "Le produit est arrivé endommagé et le support était inutile.",
            "Expérience terrible. J'ai attendu 3 semaines pour rien.",
            "Qualité médiocre. Cassé après deux semaines d'utilisation.",
        ],
        "neutral": [
            "Le produit fonctionne comme décrit. Rien de spécial.",
            "Expérience moyenne. Livraison à temps.",
        ],
    },
    "de": {
        "positive": [
            "Ich liebe dieses Produkt! Bester Kauf den ich je gemacht habe.",
            "Der Kundenservice war unglaublich hilfreich.",
            "Ausgezeichnete Qualität, schneller Versand. Sehr empfehlenswert!",
        ],
        "negative": [
            "Das Produkt kam beschädigt an und der Support war nutzlos.",
            "Schreckliche Erfahrung. 3 Wochen gewartet ohne Ergebnis.",
            "Schlechte Qualität. Nach zwei Wochen kaputt gegangen.",
        ],
        "neutral": [
            "Das Produkt funktioniert wie beschrieben. Nichts Besonderes.",
        ],
    },
    "ja": {
        "positive": [
            "この製品が大好きです！最高の買い物でした。",
            "カスタマーサービスが非常に親切で助かりました。",
            "素晴らしい品質です。強くお勧めします！",
        ],
        "negative": [
            "製品が破損して届きました。サポートも役に立ちませんでした。",
            "ひどい経験でした。3週間待っても届きませんでした。",
        ],
        "neutral": [
            "製品は説明通りに動作します。特別なものはありません。",
        ],
    },
}

SOURCES = ["app_store", "play_store", "email", "chat", "survey", "twitter", "support_ticket", "web_form"]


def generate_demo_data(n: int = 500, seed: int = 42) -> list[dict]:
    random.seed(seed)
    entries = []
    base_date = datetime(2024, 1, 1)

    # Create a sentiment drift: starts positive, dips in middle, recovers
    for i in range(n):
        progress = i / n

        # Sentiment distribution changes over time
        if progress < 0.3:
            weights = {"positive": 0.6, "negative": 0.15, "neutral": 0.25}
        elif progress < 0.5:
            weights = {"positive": 0.2, "negative": 0.55, "neutral": 0.25}
        elif progress < 0.7:
            weights = {"positive": 0.15, "negative": 0.6, "neutral": 0.25}
        else:
            weights = {"positive": 0.55, "negative": 0.2, "neutral": 0.25}

        sentiment = random.choices(
            list(weights.keys()), weights=list(weights.values()), k=1
        )[0]

        # Language distribution: mostly English with some variety
        lang_weights = {"en": 0.5, "es": 0.15, "fr": 0.15, "de": 0.1, "ja": 0.1}
        lang = random.choices(
            list(lang_weights.keys()), weights=list(lang_weights.values()), k=1
        )[0]

        templates = FEEDBACK_TEMPLATES[lang][sentiment]
        text = random.choice(templates)

        # Add some variation
        if random.random() < 0.3:
            suffixes = {
                "en": [" Overall rating: {}/5.", " Would rate {}/10.", " Score: {}/5."],
                "es": [" Puntuación: {}/5.", " Calificación: {}/10."],
                "fr": [" Note: {}/5.", " Évaluation: {}/10."],
                "de": [" Bewertung: {}/5.", " Note: {}/10."],
                "ja": [" 評価: {}/5。", " スコア: {}/10。"],
            }
            rating = {"positive": random.randint(4, 5), "negative": random.randint(1, 2), "neutral": random.randint(3, 3)}
            suffix = random.choice(suffixes.get(lang, suffixes["en"]))
            text += suffix.format(rating[sentiment])

        timestamp = base_date + timedelta(
            days=int(progress * 180),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        entries.append({
            "id": uuid.uuid4().hex[:12],
            "text": text,
            "source": random.choice(SOURCES),
            "timestamp": timestamp.isoformat(),
            "rating": {"positive": random.randint(4, 5), "negative": random.randint(1, 2), "neutral": 3}[sentiment],
        })

    return entries


def save_demo_data(output_dir: str = ".") -> dict[str, str]:
    """Generate and save demo data in multiple formats."""
    entries = generate_demo_data(500)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    files = {}

    # CSV
    csv_path = output_path / "demo_feedback.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "text", "source", "timestamp", "rating"])
        writer.writeheader()
        writer.writerows(entries)
    files["csv"] = str(csv_path)

    # JSON
    json_path = output_path / "demo_feedback.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    files["json"] = str(json_path)

    print(f"Generated {len(entries)} demo entries")
    print(f"CSV:  {csv_path}")
    print(f"JSON: {json_path}")

    return files


if __name__ == "__main__":
    save_demo_data("./demo_data")
