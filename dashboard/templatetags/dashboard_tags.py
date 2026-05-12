from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_com_param(context, **kwargs):
    """
    Retorna a query string atual substituindo/adicionando os parâmetros
    passados como keyword arguments.

    Uso: {% url_com_param categoria='registro_civil' p=1 %}
    """
    request = context.get('request')
    if request is None:
        params = kwargs
    else:
        params = request.GET.copy()
        for key, value in kwargs.items():
            if value == '' or value is None:
                params.pop(key, None)
            else:
                params[key] = value

    qs = params.urlencode()
    return f'?{qs}' if qs else '?'
