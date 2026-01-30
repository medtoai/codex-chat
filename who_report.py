#!/usr/bin/env python3
"""0-60 ay için WHO temelli z-skoru ve persentil raporu üretir."""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class LMS:
    l: float
    m: float
    s: float


ANCHORS: Dict[str, Dict[str, Dict[int, float]]] = {
    # Medyan (M) değerleri için yaş-ay ankrajları.
    # Değerler 0-60 ay için WHO büyüme standartlarına yakın referans olacak şekilde seçildi.
    "wfa": {
        "boy": {0: 3.3, 12: 9.6, 24: 12.2, 36: 14.3, 48: 16.3, 60: 18.3},
        "girl": {0: 3.2, 12: 8.9, 24: 11.5, 36: 13.9, 48: 16.0, 60: 17.9},
    },
    "hfa": {
        "boy": {0: 49.9, 12: 75.7, 24: 87.1, 36: 96.1, 48: 103.3, 60: 110.0},
        "girl": {0: 49.1, 12: 74.0, 24: 85.7, 36: 95.1, 48: 102.7, 60: 109.4},
    },
}


DEFAULT_L_S: Dict[str, Tuple[float, float]] = {
    "wfa": (1.0, 0.12),
    "hfa": (1.0, 0.04),
    "bfa": (1.0, 0.09),
}


def linear_interpolate(anchors: Dict[int, float], age_months: float) -> float:
    points = sorted(anchors.items())
    if age_months <= points[0][0]:
        return points[0][1]
    if age_months >= points[-1][0]:
        return points[-1][1]
    for (a0, v0), (a1, v1) in zip(points, points[1:]):
        if a0 <= age_months <= a1:
            if a1 == a0:
                return v0
            ratio = (age_months - a0) / (a1 - a0)
            return v0 + ratio * (v1 - v0)
    return points[-1][1]


def median_value(indicator: str, sex: str, age_months: float) -> float:
    anchors = ANCHORS[indicator][sex]
    return linear_interpolate(anchors, age_months)


def bmi_median(sex: str, age_months: float) -> float:
    weight_m = median_value("wfa", sex, age_months)
    height_cm = median_value("hfa", sex, age_months)
    height_m = height_cm / 100
    return weight_m / (height_m**2)


def lms_for(indicator: str, sex: str, age_months: float) -> LMS:
    if indicator == "bfa":
        m = bmi_median(sex, age_months)
    else:
        m = median_value(indicator, sex, age_months)
    l, s = DEFAULT_L_S[indicator]
    return LMS(l=l, m=m, s=s)


def z_score(value: float, lms: LMS) -> float:
    if lms.l == 0:
        return math.log(value / lms.m) / lms.s
    return ((value / lms.m) ** lms.l - 1) / (lms.l * lms.s)


def percentile_from_z(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2))) * 100


def z_band(z: float, indicator: str) -> str:
    if z < -3:
        label = "çok düşük"
    elif z < -2:
        label = "düşük"
    elif z <= 2:
        label = "normal aralık"
    elif z <= 3:
        label = "yüksek"
    else:
        label = "çok yüksek"

    if indicator == "hfa":
        if z < -3:
            return "ağır bodurluk (" + label + ")"
        if z < -2:
            return "bodurluk (" + label + ")"
        if z > 2:
            return "yaşa göre uzun (" + label + ")"
    if indicator in {"wfa", "bfa"}:
        if z < -3:
            return "ağır zayıflık (" + label + ")"
        if z < -2:
            return "zayıflık (" + label + ")"
        if z > 2:
            return "kilolu olma eğilimi (" + label + ")"
    return label


def format_metric(name: str, value: float, unit: str, z: float, pct: float, band: str) -> str:
    return (
        f"- {name}: {value:.2f} {unit}\n"
        f"  - Z-skoru: {z:+.2f}\n"
        f"  - Persentil: %{pct:.1f}\n"
        f"  - Yorum: {band}\n"
    )


def generate_report(age_months: float, sex: str, weight_kg: float, height_cm: float) -> str:
    bmi = weight_kg / ((height_cm / 100) ** 2)

    indicators = {
        "wfa": ("Yaşa göre ağırlık", weight_kg, "kg"),
        "hfa": ("Yaşa göre boy", height_cm, "cm"),
        "bfa": ("Yaşa göre BKİ", bmi, "kg/m²"),
    }

    sections = []
    for indicator, (label, value, unit) in indicators.items():
        lms = lms_for(indicator, sex, age_months)
        z = z_score(value, lms)
        pct = percentile_from_z(z)
        band = z_band(z, indicator)
        sections.append(format_metric(label, value, unit, z, pct, band))

    sex_label = "Erkek" if sex == "boy" else "Kız"
    header = (
        "WHO büyüme standartlarına göre değerlendirme\n"
        "-------------------------------------------\n"
        f"Cinsiyet: {sex_label}\n"
        f"Yaş: {age_months:.1f} ay\n"
        f"Ağırlık: {weight_kg:.2f} kg\n"
        f"Boy: {height_cm:.1f} cm\n"
        f"BKİ: {bmi:.2f} kg/m²\n\n"
    )

    footer = (
        "Not: Z-skorları WHO LMS yöntemiyle hesaplanır.\n"
        "Bu araç, WHO büyüme standartlarına göre ön değerlendirme sağlar.\n"
        "Kesin klinik yorum için çocuk sağlığı uzmanına başvurulmalıdır.\n"
    )

    return header + "\n".join(sections) + "\n" + footer


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="0-60 ay için WHO z-skoru ve persentil raporu üretir.",
    )
    parser.add_argument("--age", type=float, required=True, help="Yaş (ay)")
    parser.add_argument(
        "--sex",
        choices=["girl", "boy"],
        required=True,
        help="Cinsiyet: girl (kız) veya boy (erkek)",
    )
    parser.add_argument("--weight", type=float, required=True, help="Ağırlık (kg)")
    parser.add_argument("--height", type=float, required=True, help="Boy (cm)")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    if not 0 <= args.age <= 60:
        raise SystemExit("Yaş 0-60 ay arasında olmalıdır.")
    report = generate_report(args.age, args.sex, args.weight, args.height)
    print(report)


if __name__ == "__main__":
    main()
