from django import template
from ..models import MenuItem

register = template.Library()


@register.inclusion_tag('menu_app/menu.html', takes_context=True)
def draw_menu(context, menu_name):
    request = context['request']
    current_url = request.path

    menu_items = MenuItem.objects.filter(
        menu_name=menu_name
    ).select_related('parent')
    items_dict = convert_queryset_to_dict(menu_items)
    active_item = find_active_item(items_dict, current_url)
    menu_tree = build_tree_structure(items_dict)
    if active_item:
        expand_active_path(menu_tree, active_item)

    return {
        'menu_tree': menu_tree,
        'menu_name': menu_name,
    }


def convert_queryset_to_dict(menu_items):
    items_dict = {}
    for item in menu_items:
        items_dict[item.id] = {
            'id': item.id,
            'name': item.name,
            'url': item.get_url(),
            'parent_id': item.parent_id,
            'children': [],
            'is_active': False,
            'is_expanded': False,
        }
    return items_dict


def find_active_item(items_dict, current_url):
    for item_data in items_dict.values():
        if item_data['url'] == current_url:
            item_data['is_active'] = True
            return item_data
    return None


def build_tree_structure(items_dict):
    root_items = []

    for item_id, item_data in items_dict.items():
        if item_data['parent_id'] is None:
            root_items.append(item_data)
        else:
            parent = items_dict.get(item_data['parent_id'])
            if parent:
                parent['children'].append(item_data)

    return root_items


def expand_active_path(menu_tree, active_item):
    def find_path_to_active(items, target_id, current_path=None):
        if current_path is None:
            current_path = []
        for item in items:
            if item['id'] == target_id:
                return current_path + [item]
            if item['children']:
                result = find_path_to_active(item['children'], target_id, current_path + [item])
                if result:
                    return result
        return None

    path_to_active = find_path_to_active(menu_tree, active_item['id'])
    if path_to_active:
        for item in path_to_active[:-1]:
            item['is_expanded'] = True

        active_item['is_expanded'] = True
