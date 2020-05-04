import json


def get_menu_dict():
  menu = open('api/assets/full-menu.json')
  return json.load(menu)


def get_item_dict(item_id):
  item = open(f'api/assets/items/{item_id}.json')

  return json.load(item)
