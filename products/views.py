import json

from django.http      import JsonResponse
from django.views     import View
from django.db.models import Q, Count, Sum

from products.models  import Product, Menu

class CategoryView(View):
    def get(self, reqeust):
        menus = Menu.objects.all()

        category_list = [{
            'menu_id'      : menu.id,
            'menu_name'    : menu.name,
            'main_category': [{
                'main_category_id'  : main_category.id,
                'main_category_name': main_category.name,
                'category'          : [{
                    'category_id'  : category.id,
                    'category_name': category.name,
                } for category in main_category.category_set.all()]
            } for main_category in menu.maincategory_set.all()]
        } for menu in menus]

        return JsonResponse({"results" : category_list}, status=200)

class ProductListView(View):
    def get(self, request):
        menu          = request.GET.get('menu', None)
        main_category = request.GET.get('main_category', None)
        category      = request.GET.get('category', None)
        search        = request.GET.get('search')
        sort          = request.GET.get('sort', 'new')
        limit         = int(request.GET.get('limit', 12))
        offset        = int(request.GET.get('offset',0))

        q = Q()

        if menu:
            q &= Q(categoryproduct__category__main_category__menu__id = menu)

        if main_category:
            q &= Q(categoryproduct__category__main_category__id = main_category)

        if category:
            q &= Q(categoryproduct__category__id = category)

        if search:
            q &= Q(name__icontains = search)

        sort_type = {
            'reviews'   : '-total_reviews',
            'sales'     : '-total_sales',
            'new'       : '-id',
            'price_desc': '-price',
            'price_asc' : 'price'
            }

        products = Product.objects.filter(q).annotate(total_sales=Sum('orderitem__quantity', distinct=True))\
            .annotate(total_reviews=Count('review__id', distinct=True))\
            .order_by(sort_type.get(sort))[offset:offset+limit]
        
        products_list = [{
                "id"           : product.id,
                "name"         : product.name,
                "price"        : product.price,
                "discount_rate": product.discount_rate,
                "novel"        : True if product in Product.objects.all().order_by('-id')[:2] else False,
                "sale_or_not"  : False if product.discount_rate == 0 else True,
                "img_url"      : [image.img_url for image in product.productimage_set.all()],
        } for product in products]

        return JsonResponse({'results': products_list}, status=200)

class ProductDetailView(View):
    def get(self, request, *args, **kwargs):
        try:
            product = Product.objects.prefetch_related('productimage_set').get(id=kwargs["product_id"])
            product_detail = {
                    "id"          : product.id,
                    "img"         : [image.img_url for image in product.productimage_set.all()][0],
                    "name"        : product.name,
                    "price"       : product.price,
                    "salePercent" : product.discount_rate,
                    "novel"       : True if product in Product.objects.all().order_by('-id')[:2] else False,
                    "sale"        : False if product.discount_rate == 0 else True,
                    "description" : product.description,
                    "subCategory" : product.categoryproduct_set.filter().last().category.name,
                    "mainCategory": product.categoryproduct_set.filter().last().category.main_category.name,
            }

            return JsonResponse({'results' : product_detail}, status=200)

        except KeyError:
            return JsonResponse({"message" : "KEY_ERROR"}, status=401)
        except Product.DoesNotExist:
            return JsonResponse({"message" : "PRODUCT_DOES_NOT_EXIST"}, status = 404)

class RecommendationView(View):
    def get(self, request):
        limit                  = int(request.GET.get('limit', 4))
        offset                 = int(request.GET.get('offset',0))
        recommendations        = Product.objects.all().prefetch_related('productimage_set').order_by("?")[offset:offset+limit]
        product_recommendation = [{
                "id"     : recommendation.id,
                "img_url": [image.img_url for image in recommendation.productimage_set.all()],
                "name"   : recommendation.name,
                "price"  : recommendation.price,
        } for recommendation in recommendations]
        
        return JsonResponse({'results' : product_recommendation}, status=200)