from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
import phonenumbers
from phonenumbers import NumberParseException

from .models import Product
from .models import Order
from .models import OrderItem


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def validate_phone_number(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number, "RU")
        return phonenumbers.is_valid_number(parsed_number)
    except NumberParseException:
        return False


@api_view(['POST'])
def register_order(request):
    try:
        order_properties = request.data

        required_fields = ['products', 'firstname', 'lastname', 'phonenumber', 'address']
        for field in required_fields:
            if field not in order_properties:
                return Response(
                    {'error': f'{field}: Пропущенно обязательное поле.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if order_properties[field] is None:
                return Response(
                    {'error': f'{field}: Это поле не может быть пустым.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        if not isinstance(order_properties['firstname'], str):
            return Response(
                    {'error': 'firstname: Not a valid string.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if not validate_phone_number(order_properties['phonenumber']):
            return Response(
                {'error': 'phonenumber: Введен некорректный номер телефона.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        products_properties = order_properties['products']

        if isinstance(products_properties, str):
            return Response(
                {'error': 'products: Ожидался list со значениями, но был получен str'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if products_properties is None:
            return Response(
                {'error': 'products: Это поле не может быть пустым'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(products_properties, list):
            return Response(
                {'error': f'products: Ожидался list со значениями'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(products_properties) == 0:
            return Response(
                {'error': 'products: Этот список не может быть пустым'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order = Order.objects.create(
            first_name=order_properties['firstname'],
            last_name=order_properties['lastname'],
            phone_number=order_properties['phonenumber'],
            address=order_properties['address']
        )

        for item in order_properties['products']:
            product = Product.objects.get(id=item['product'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.get('quantity', 1)
            )
    except ObjectDoesNotExist:
        order.delete()
        return Response(
            {'error': f'{item["product"]}: Продукт с этим id не найден'},
            status=status.HTTP_400_BAD_REQUEST)
    return Response({'order_id': order.id}, status=status.HTTP_201_CREATED)
