from rest_framework import serializers
from .models import Category, TipoServico, Product


class TipoServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoServico
        fields = ['id', 'name', 'slug', 'description', 'order']


class CategorySerializer(serializers.ModelSerializer):
    total_servicos = serializers.IntegerField(
        source='active_products_count', read_only=True
    )

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon_svg', 'order', 'is_active', 'total_servicos']


class ServicoSerializer(serializers.ModelSerializer):
    categoria = CategorySerializer(source='category', read_only=True)
    tipo = TipoServicoSerializer(read_only=True)
    categoria_slug = serializers.SlugRelatedField(
        source='category', slug_field='slug', read_only=True
    )
    tipo_slug = serializers.SlugRelatedField(
        source='tipo', slug_field='slug', read_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'categoria',
            'categoria_slug',
            'tipo',
            'tipo_slug',
            'short_description',
            'description',
            'delivery_days',
            'is_active',
            'is_featured',
            'order',
            'created_at',
        ]
