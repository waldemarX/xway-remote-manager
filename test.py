import requests
import traceback

a = requests.get('http://api.pim.dev.x-way.io/cabinet/')

try:
    print(a.json())
except requests.exceptions.JSONDecodeError as e:
    print(traceback.format_exc())