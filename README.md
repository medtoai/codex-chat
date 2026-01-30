# WHO Büyüme Standartları Rapor Aracı

Bu araç, 0-60 ay aralığında kız ve erkek çocuklar için **yaşa göre ağırlık**, **yaşa göre boy** ve **yaşa göre BKİ** z-skoru ile persentil değerlerini üretir.

## Kurulum

Python 3.10+ gerektirir. Ek bağımlılık yoktur.

## Kullanım

```bash
python who_report.py --age 24 --sex girl --weight 11.2 --height 84.5
```

## Notlar

- Z-skorları WHO LMS yöntemine dayanır.
- Median değerler (M), WHO büyüme standartlarıyla uyumlu olacak şekilde seçilmiş ankrajlardan doğrusal olarak türetilir.
- Klinik kararlar için mutlaka çocuk sağlığı uzmanına danışılmalıdır.
