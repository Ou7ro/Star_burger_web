from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings

from geopy import distance
import requests

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def fetch_coordinates(apikey, address):
    if not address:
        return None
    
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lat, lon


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    yandex_api_key = settings.YANDEX_API_KEY
    orders = Order.objects.total_price().filter(status='unprocessed').prefetch_related(
        'order_items__product__menu_items__restaurant'
    )

    menu_items = RestaurantMenuItem.objects.filter(availability=True).select_related('restaurant', 'product')

    product_restaurants = {}
    for item in menu_items:
        if item.product_id not in product_restaurants:
            product_restaurants[item.product_id] = []
        product_restaurants[item.product_id].append(item.restaurant)

    orders_with_restaurants = []
    for order in orders:
        suitable_restaurants = set()
        first_product = True

        for order_item in order.order_items.all():
            product = order_item.product
            if product.id in product_restaurants:
                if first_product:
                    suitable_restaurants = set(product_restaurants[product.id])
                    first_product = False
                else:
                    suitable_restaurants &= set(product_restaurants[product.id])
            else:
                suitable_restaurants = set()
                break

        order_coords = None
        if order.address:
            order_coords = fetch_coordinates(yandex_api_key, order.address)

        restaurants_with_distances = []
        for restaurant in suitable_restaurants:
            if (restaurant.lat is not None and restaurant.lon is not None and 
                order_coords is not None):

                try:
                    rest_order_distance = distance.distance(
                        order_coords,
                        (restaurant.lat, restaurant.lon)
                    ).km
                    distance_km = f'{round(rest_order_distance, 2)} км'
                except ValueError:
                    distance_km = 'Ошибка расчета расстояния'
            else:
                distance_km = 'Ошибка определения координат'

            restaurants_with_distances.append({
                'restaurant': restaurant,
                'distance': distance_km
            })

        restaurants_with_distances.sort(key=lambda x: 
            x['distance'] if isinstance(x['distance'], (int, float)) else float('inf'))

        orders_with_restaurants.append({
            'order': order,
            'suitable_restaurants': restaurants_with_distances,
        })

    return render(request, template_name='order_items.html', context={
        'order_items': orders_with_restaurants
    })
