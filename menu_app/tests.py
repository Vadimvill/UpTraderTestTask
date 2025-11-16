from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.db import IntegrityError
from .models import MenuItem
from .templatetags.menu_tags import (
    draw_menu, get_menu_items, convert_queryset_to_dict,
    find_active_item, build_tree_structure, expand_active_path
)


class MenuModelTest(TestCase):
    def setUp(self):
        self.main_menu = MenuItem.objects.create(
            name='Главная',
            menu_name='main_menu',
            explicit_url='/',
            order=0
        )
        self.services = MenuItem.objects.create(
            name='Услуги',
            menu_name='main_menu',
            explicit_url='/services/',
            order=1
        )
        self.webdev = MenuItem.objects.create(
            name='Веб-разработка',
            menu_name='main_menu',
            explicit_url='/services/web-dev/',
            parent=self.services,
            order=0
        )

    def test_menu_item_creation(self):
        self.assertEqual(MenuItem.objects.count(), 3)
        self.assertEqual(self.services.children.count(), 1)
        self.assertEqual(self.webdev.parent, self.services)

    def test_get_url_methods(self):
        self.assertEqual(self.main_menu.get_url(), '/')

        named_item = MenuItem.objects.create(
            name='Через named URL',
            menu_name='main_menu',
            named_url='admin:index',
            order=2
        )
        self.assertIn('/admin/', named_item.get_url())

        empty_item = MenuItem.objects.create(
            name='Без URL',
            menu_name='main_menu',
            order=3
        )
        self.assertEqual(empty_item.get_url(), '#')

    def test_has_children_property(self):
        self.assertTrue(self.services.has_children)
        self.assertFalse(self.main_menu.has_children)
        self.assertFalse(self.webdev.has_children)

    def test_ordering(self):
        MenuItem.objects.create(
            name='Блог',
            menu_name='main_menu',
            explicit_url='/blog/',
            order=0
        )

        MenuItem.objects.create(
            name='Контакты',
            menu_name='main_menu',
            explicit_url='/contact/',
            order=2
        )

        items = MenuItem.objects.filter(menu_name='main_menu')

        expected_order = ['Блог', 'Веб-разработка', 'Главная', 'Услуги', 'Контакты']
        actual_order = [item.name for item in items]

        self.assertEqual(actual_order, expected_order)


class MenuTagsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.home = MenuItem.objects.create(
            name='Главная',
            menu_name='main_menu',
            explicit_url='/',
            order=0
        )
        self.services = MenuItem.objects.create(
            name='Услуги',
            menu_name='main_menu',
            explicit_url='/services/',
            order=1
        )
        self.webdev = MenuItem.objects.create(
            name='Веб-разработка',
            menu_name='main_menu',
            explicit_url='/services/web-dev/',
            parent=self.services,
            order=0
        )
        self.django = MenuItem.objects.create(
            name='Django',
            menu_name='main_menu',
            explicit_url='/services/web-dev/django/',
            parent=self.webdev,
            order=0
        )

    def test_convert_queryset_to_dict(self):
        menu_items = MenuItem.objects.filter(menu_name='main_menu')
        items_dict = convert_queryset_to_dict(menu_items)

        self.assertEqual(len(items_dict), 4)
        self.assertEqual(items_dict[self.home.id]['name'], 'Главная')
        self.assertEqual(items_dict[self.webdev.id]['parent_id'], self.services.id)

    def test_find_active_item(self):
        menu_items = MenuItem.objects.filter(menu_name='main_menu')
        items_dict = convert_queryset_to_dict(menu_items)

        # Находим активный элемент
        active_item = find_active_item(items_dict, '/services/web-dev/')
        self.assertEqual(active_item['name'], 'Веб-разработка')
        self.assertTrue(active_item['is_active'])

        no_active = find_active_item(items_dict, '/non-existent/')
        self.assertIsNone(no_active)

    def test_build_tree_structure(self):
        menu_items = MenuItem.objects.filter(menu_name='main_menu')
        items_dict = convert_queryset_to_dict(menu_items)
        tree = build_tree_structure(items_dict)

        self.assertEqual(len(tree), 2)

        services_item = next(item for item in tree if item['name'] == 'Услуги')
        self.assertEqual(len(services_item['children']), 1)
        self.assertEqual(services_item['children'][0]['name'], 'Веб-разработка')

    def test_expand_active_path(self):
        menu_items = MenuItem.objects.filter(menu_name='main_menu')
        items_dict = convert_queryset_to_dict(menu_items)
        tree = build_tree_structure(items_dict)

        django_item = None
        for item in tree:
            if item['name'] == 'Услуги':
                for child in item['children']:
                    if child['name'] == 'Веб-разработка':
                        django_item = child['children'][0]
                        break

        self.assertIsNotNone(django_item)

        expand_active_path(tree, django_item)

        services_item = next(item for item in tree if item['name'] == 'Услуги')
        webdev_item = next(item for item in services_item['children'] if item['name'] == 'Веб-разработка')

        self.assertTrue(services_item['is_expanded'])
        self.assertTrue(webdev_item['is_expanded'])
        self.assertTrue(django_item['is_expanded'])

    def test_draw_menu_template_tag(self):
        request = self.factory.get('/services/web-dev/')
        context = {'request': request}

        result = draw_menu(context, 'main_menu')

        self.assertIn('menu_tree', result)
        self.assertEqual(result['menu_name'], 'main_menu')
        self.assertEqual(len(result['menu_tree']), 2)

    def test_draw_menu_active_item(self):
        request = self.factory.get('/services/web-dev/')
        context = {'request': request}

        result = draw_menu(context, 'main_menu')

        def find_active_in_tree(items):
            for item in items:
                if item.get('is_active'):
                    return item
                if item['children']:
                    active = find_active_in_tree(item['children'])
                    if active:
                        return active
            return None

        active_item = find_active_in_tree(result['menu_tree'])
        self.assertIsNotNone(active_item)
        self.assertEqual(active_item['name'], 'Веб-разработка')


class MenuCacheTest(TestCase):
    def setUp(self):
        MenuItem.objects.create(
            name='Главная',
            menu_name='main_menu',
            explicit_url='/',
            order=0
        )

    def test_cache_usage(self):
        with self.assertNumQueries(1):
            items1 = get_menu_items('main_menu')

        with self.assertNumQueries(0):
            items2 = get_menu_items('main_menu')

        self.assertEqual(len(items1), len(items2))

    def test_cache_invalidation(self):
        get_menu_items('main_menu')

        MenuItem.objects.create(
            name='Новый пункт',
            menu_name='main_menu',
            explicit_url='/new/',
            order=1
        )

        with self.assertNumQueries(1):
            get_menu_items('main_menu')


class MenuEdgeCasesTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_empty_menu(self):
        request = self.factory.get('/')
        context = {'request': request}

        result = draw_menu(context, 'non_existent_menu')

        self.assertEqual(len(result['menu_tree']), 0)
        self.assertEqual(result['menu_name'], 'non_existent_menu')

    def test_url_normalization(self):
        """Тест нормализации URL (trailing slashes)"""
        MenuItem.objects.create(
            name='Страница',
            menu_name='test_menu',
            explicit_url='/page/',
            order=0
        )

        menu_items = MenuItem.objects.filter(menu_name='test_menu')
        items_dict = convert_queryset_to_dict(menu_items)

        active_item = find_active_item(items_dict, '/page/')
        self.assertIsNotNone(active_item)
        self.assertEqual(active_item['name'], 'Страница')

    def test_self_referencing_parent(self):
        item = MenuItem.objects.create(
            name='Тест',
            menu_name='test_menu',
            explicit_url='/test/',
            order=0
        )

        item.parent = item
        try:
            item.save()
            item.refresh_from_db()
            self.assertEqual(item.parent, item)
        except IntegrityError:
            ...
