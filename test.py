# import inspect
# from optparse import OptionParser
#
# class A:
#     COMMAND_A = 1
#     COMMAND_B = 2
#     COMMAND_C = 3
#
#     def __init__(self):
#         self.comm = 4
#
#
#     def perform_push(self):
#         print("hello world")
#
#
#
# a = A()
#
# for attribute, value in a.__dict__.items():
#     print(f"{attribute} ===== {value}")
#
# atttrs = inspect.getmembers(a, lambda a: not(inspect.isroutine(a)))
#
# print([b for b in atttrs if not(b[0].startswith('__') and b[0].endswith('__'))])
#
#
# print([i for i in A.__dict__.items() if not i[0].startswith('_')])
# print('execute_command_help'.replace('execute_', ''))



# import xml.etree.ElementTree as ET
#
# valid_offer_ids = []
# tree = ET.parse("/home/vladimir/python/stock.xml")
# root = tree.getroot()
#
# for data in root[0]:
#     if data.tag.startswith("offer"):
#         for offer in data:
#             for offer_data in offer:
#                 if offer_data.tag.startswith("param") and offer_data.attrib.get("name") == "quantity":
#                     if int(offer_data.text) >= 1:
#                         valid_offer_ids.append(offer.attrib.get("id"))
# print(valid_offer_ids)


# import pandas as pd
#
# xlsx = pd.read_excel('/home/vladimir/python/mvm_codes.xlsx')
#
# eldo_codes_mapping = xlsx.columns[1]
# mvm_codes_mapping = xlsx.columns[2]
#
# codes = {}
#
# iters = 0
# for _, row in xlsx.iterrows():
#     iters += 1
#     if iters > 100:
#         break
#
#     if isinstance(row[eldo_codes_mapping], int):
#         codes[row[eldo_codes_mapping]] = row[mvm_codes_mapping]
#
# print(codes)






a = {
    1: 2
}
b = {
    6: 5,
    1: 6
}

a.update(b)
print(a)





