from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filtro para obtener un elemento de un diccionario usando una clave
    Uso en template: {{ mi_diccionario|get_item:mi_clave }}
    """
    if isinstance(dictionary, dict):
        # Convertir la clave a int si es necesario (para bimestres)
        try:
            key = int(key)
        except (ValueError, TypeError):
            pass
        return dictionary.get(key, [])
    return []

@register.filter
def mul(value, arg):
    """
    Multiplica dos valores
    Uso: {{ valor|mul:2 }}
    """
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0