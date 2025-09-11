from rest_framework import serializers
from .models import Order, OrderItem, Product
from django.core.validators import MinValueValidator, MaxValueValidator
from phonenumber_field.serializerfields import PhoneNumberField


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        error_messages={'does_not_exist': 'Продукт с этим id не найден'}
    )
    quantity = serializers.IntegerField(
        validators=[
            MinValueValidator(1, message='Количество должно быть не менее 1'),
            MaxValueValidator(99, message='Количество должно быть не более 99')
        ]
    )

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    products = OrderItemSerializer(many=True, write_only=True, allow_empty=False)
    firstname = serializers.CharField(max_length=50)
    lastname = serializers.CharField(max_length=50)
    address = serializers.CharField(max_length=50)
    phonenumber = PhoneNumberField()

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']
        read_only_fields = ['id']

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)

        for product_data in products_data:
            OrderItem.objects.create(
                order=order,
                product=product_data['product'],
                quantity=product_data['quantity']
            )
        return order


class OrderResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address']
