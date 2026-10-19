import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='markdown')
@register.filter(name='render_markdown')
def render_markdown(text):
    if not text:
        return ""
    # Normalize list items that directly follow regular text without empty line
    raw_str = str(text)
    normalized = re.sub(r'([^\n])\n(\s*[-*+]\s+)', r'\1\n\n\2', raw_str)
    normalized = re.sub(r'([^\n])\n(\s*\d+\.\s+)', r'\1\n\n\2', normalized)
    try:
        import markdown
        html = markdown.markdown(normalized, extensions=['extra', 'nl2br', 'sane_lists'])
    except Exception:
        import html as html_lib
        html = html_lib.escape(raw_str).replace('\n', '<br>')
    return mark_safe(html)
