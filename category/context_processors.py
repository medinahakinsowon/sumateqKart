

from .models import Category

def menu_links(requet):
  links = Category.objects.all()
  return dict(links=links)