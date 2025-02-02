from django import template

register = template.Library()

@register.filter
def is_video(file_url):
    video_extensions = ['.mp4', '.webm', '.ogg']
    return any(file_url.lower().endswith(ext) for ext in video_extensions)

@register.filter
def is_image(file_url):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    return any(file_url.lower().endswith(ext) for ext in image_extensions)
