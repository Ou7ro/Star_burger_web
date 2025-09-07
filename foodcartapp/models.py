from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import Sum, F
from django.utils import timezone


class CustomQueryset(models.QuerySet):
    def total_price(self):
        price = self.annotate(
            total_price=Sum(
                F('order_items__price') * F('order_items__quantity')
            )
        )
        return price


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('unprocessed', 'Необработанный'),
        ('underway', 'В работе'),
        ('delivery', 'Доставка'),
        ('completed', 'Завершен'),
    ]
    PAYMANT_CHOICES = [
        ('cash', 'Наличностью'),
        ('electronic', 'Электронно')
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unprocessed',
        db_index=True,
        verbose_name='Статус'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMANT_CHOICES,
        default='Не выбран',
        db_index=True,
        verbose_name='Способ оплаты'
    )
    address = models.CharField(
        'адрес',
        max_length=50,
    )
    firstname = models.CharField(
        'имя',
        max_length=50
    )
    lastname = models.CharField(
        'фамилия',
        max_length=50,
        db_index=True,
    )
    phonenumber = PhoneNumberField(
        'номер телефона',
        region='RU',
        max_length=20,
        db_index=True
    )
    comments = models.TextField(
        'комментарий',
        blank=True,
    )
    registated_at = models.DateTimeField(
        'дата и время регистрации',
        default=timezone.now,
        db_index=True
    )
    called_at = models.DateTimeField(
        'дата и время прозвона',
        null=True,
        blank=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        'дата и время доставки',
        null=True,
        blank=True,
        db_index=True
    )
    objects = CustomQueryset.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ от {self.firstname} {self.lastname}, по адресу: {self.address}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              related_name='order_items',
                              verbose_name='заказ')
    product = models.ForeignKey(Product,
                                on_delete=models.CASCADE,
                                related_name='order_items',
                                verbose_name='продукт',
                                blank=True)
    quantity = models.IntegerField(
        validators=[MinValueValidator(1),
                    MaxValueValidator(99)],
        verbose_name='количество',
        blank=True)
    price = models.DecimalField(
        verbose_name='цена на момент заказа',
        max_digits=8,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'
