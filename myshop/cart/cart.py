from decimal import Decimal
from django.conf import settings
from shop.models import Product
from coupons.models import Coupons




class Cart:

    def __init__(self, request):
        """
        Инициализация корзины.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # сохранение пустой корзины в сессии
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        # Сохраняем купон.
        self.coupon_id = self.session.get('coupon_id')

    def __iter__(self):
        """
        Перебор элементов корзины и получение товара из бд
        """
        product_ids = self.cart.keys()
        # получение обьектов продуктов и добавление их в корзину
        products = Product.objects.filter(id__in=product_ids)

        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Считаем все объекты в корзине.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def add(self, product, quantity=1, update_quantity=False):
        """
        Добавление продукта в корзину и изменение количества(quantity).
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0,
                                     'price': str(product.price)}
        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        # помечаем сессию как "modified" ,чтобы убедиться что она будет сохранена
        self.session.modified = True

    def remove(self, product):
        """
        Удаление продукта из корзины.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        # Удаление корзины из сессии
        del self.session[settings.CART_SESSION_ID]
        self.save()

    @property
    def coupon(self):
        if self.coupon_id:
            return Coupons.objects.get(id=self.coupon_id)
        return None

    def get_discount(self):
        if self.coupon:
            return (self.coupon.discount / Decimal('100')) \
                   * self.get_total_price()
        return Decimal('0')

    def get_total_price_after_discount(self):
        return self.get_total_price() - self.get_discount()