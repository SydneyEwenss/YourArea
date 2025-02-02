import re
from django.urls import reverse

def linkify_mentions(content):
    """Convert mentions in content into clickable links."""
    mention_pattern = r'@(\w+)'
    def replace_with_link(match):
        username = match.group(1)
        url = reverse('area', args=[username])
        return f'<a href="{url}">@{username}</a>'
    return re.sub(mention_pattern, replace_with_link, content)
