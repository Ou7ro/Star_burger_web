from rest_framework import serializers
from .models import Order, OrderItem, Product
from phonenumbers import parse, is_valid_number, NumberParseException


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        error_messages={'does_not_exist': 'Продукт с этим id не найден'}
    )

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError('Количество должно быть не менее 1')
        if value > 99:
            raise serializers.ValidationError('Количество должно быть не более 99')
        return value


class OrderSerializer(serializers.ModelSerializer):
    products = OrderItemSerializer(many=True, allow_empty=False)
    firstname = serializers.CharField(source='first_name', max_length=50)
    lastname = serializers.CharField(source='last_name', max_length=50)
    address = serializers.CharField(max_length=50)

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']
        extra_kwargs = {
            'phonenumber': {
                'error_messages': {
                    'invalid': 'Неверный формат номера телефона'
                }
            }
        }

    def validate_phonenumber(self, value):
        try:
            parsed_number = parse(value, 'RU')
            if not is_valid_number(parsed_number):
                raise serializers.ValidationError('Введен некорректный номер телефона')
        except NumberParseException:
            raise serializers.ValidationError('Неверный формат номера телефона')
        return value

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
