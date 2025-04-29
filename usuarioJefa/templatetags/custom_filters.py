from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filtro para acceder a los valores de un diccionario usando una clave variable.
    Uso: {{ dictionary|get_item:key }}
    """
    if not dictionary:
        return None
    
    try:
        if str(key).isdigit():
            key = int(key)
        return dictionary.get(key)
    except (KeyError, AttributeError):
        return None