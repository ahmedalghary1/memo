LATIN_DIGIT_TRANSLATION = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)


def latin_digits(value):
    """Return numeric characters using the 0-9 Latin set."""
    return str(value).translate(LATIN_DIGIT_TRANSLATION)
