EGYPT_GOVERNORATES = [
    ("القاهرة", "القاهرة"), ("الجيزة", "الجيزة"), ("الإسكندرية", "الإسكندرية"),
    ("الدقهلية", "الدقهلية"), ("البحر الأحمر", "البحر الأحمر"), ("البحيرة", "البحيرة"),
    ("الفيوم", "الفيوم"), ("الغربية", "الغربية"), ("الإسماعيلية", "الإسماعيلية"),
    ("المنوفية", "المنوفية"), ("المنيا", "المنيا"), ("القليوبية", "القليوبية"),
    ("الوادي الجديد", "الوادي الجديد"), ("السويس", "السويس"), ("أسوان", "أسوان"),
    ("أسيوط", "أسيوط"), ("بني سويف", "بني سويف"), ("بورسعيد", "بورسعيد"),
    ("دمياط", "دمياط"), ("الشرقية", "الشرقية"), ("جنوب سيناء", "جنوب سيناء"),
    ("كفر الشيخ", "كفر الشيخ"), ("مطروح", "مطروح"), ("الأقصر", "الأقصر"),
    ("قنا", "قنا"), ("شمال سيناء", "شمال سيناء"), ("سوهاج", "سوهاج"),
]

EGYPT_GOVERNORATES_EN = [
    (value, label) for (value, _), label in zip(EGYPT_GOVERNORATES, [
        "Cairo", "Giza", "Alexandria", "Dakahlia", "Red Sea", "Beheira",
        "Fayoum", "Gharbia", "Ismailia", "Monufia", "Minya", "Qalyubia",
        "New Valley", "Suez", "Aswan", "Asyut", "Beni Suef", "Port Said",
        "Damietta", "Sharqia", "South Sinai", "Kafr El Sheikh", "Matrouh",
        "Luxor", "Qena", "North Sinai", "Sohag",
    ])
]

ENGLISH_GOVERNORATES = dict(EGYPT_GOVERNORATES_EN)
