from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status


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


@api_view(['POST'])
def register_order(request):
    try:
        data = request.data

        required_fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']
        for field in required_fields:
            if field not in data:
                return Response(
                    {'error': f'Пропущенно обязательное поле: {field}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        products_data = data['products']

        if isinstance(products_data, str):
            return Response(
                {'error': 'products: Ожидался list со значениями, но был получен str'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if products_data is None:
            return Response(
                {'error': 'products: Это поле не может быть пустым'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(products_data, list):
            return Response(
                {'error': f'products: Ожидался list со значениями'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(products_data) == 0:
            return Response(
                {'error': 'products: Этот список не может быть пустым'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order = Order.objects.create(
            first_name=data['firstname'],
            last_name=data['lastname'],
            phone_number=data['phonenumber'],
            address=data['address']
        )

        for item in data['products']:
            product = Product.objects.get(id=item['product'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.get('quantity', 1)
            )
    except ObjectDoesNotExist:
        order.delete()
        return Response(
            {'error': f'Продукт с id {item["product"]} не найден'},
            status=status.HTTP_400_BAD_REQUEST)
    return Response({'order_id': order.id}, status=status.HTTP_201_CREATED)
