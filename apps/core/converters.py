class UnicodeSlugConverter:
    """Match Django slugs while allowing letters and numbers from any language."""

    regex = r"[-\w]+"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return str(value)
