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
