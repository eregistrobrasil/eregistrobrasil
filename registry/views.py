from django.http import JsonResponse
from django.views import View
from .models import Registry


class CartorioAPIView(View):
    """
    GET /api/cartorios/
    Retorna cartórios filtrados por estado, cidade e tipo de serviço.

    Parâmetros:
        estado  — UF (ex: SP)
        cidade  — nome da cidade (ex: São Paulo)
        tipo    — tipo de serviço: civil | notas | imoveis | protesto

    Resposta JSON:
        [{"id": 1, "nome": "1º Cartório de Registro Civil"}, ...]
    """

    def get(self, request):
        estado = request.GET.get('estado', '').strip().upper()
        cidade = request.GET.get('cidade', '').strip()
        tipo = request.GET.get('tipo', '').strip().lower()

        if not estado or not cidade:
            return JsonResponse([], safe=False)

        qs = Registry.objects.filter(
            estado=estado,
            cidade__iexact=cidade,
            ativo=True,
        ).only('id', 'nome')

        if tipo:
            qs = qs.filter(tipo_servico__contains=tipo)

        qs = qs.order_by('nome')

        data = [{'id': c.id, 'nome': c.nome} for c in qs]
        return JsonResponse(data, safe=False)
