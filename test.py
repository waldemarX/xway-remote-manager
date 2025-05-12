# import itertools
# import os
# import re
# import time
# from collections import defaultdict
# from dataclasses import dataclass
# from decimal import Decimal
#
# import cv2
# import numpy as np
# from PIL import Image
# from io import BytesIO
# from typing import Any
# import concurrent.futures
#
# import requests
# from pydantic import BaseModel, root_validator, model_validator, field_validator
#

# variants = {
#     'green_white': {'up': [118, 188, 33], 'down': [255, 255, 255]},
#     'red1_white': {'up': [252, 31, 36], 'down': [255, 255, 255]},
#     'red2_white': {'up': [251, 0, 0], 'down': [255, 255, 255]},
#     'black_white': {'up': [13, 16, 20], 'down': [255, 255, 255]},
#     'yellow_white': {'up': [251, 236, 49], 'down': [255, 255, 255]},
#     'grey_orange': {'up': [129, 130, 132], 'down': [252, 226, 53]}
# }

# class InfographicImageHelper:
#
#     def __init__(self):
#         # пара цветов (верхний угловой пиксель и нижний угловой пиксель)
#         self.color_pairs = []
#         # self.variants = [
#         #     [(118, 188, 33), (255, 255, 255)],
#         #     [(252, 31, 36), (255, 255, 255)],
#         #     [(251, 0, 0), (255, 255, 255)],
#         #     [(13, 16, 20), (255, 255, 255)],
#         #     [(251, 236, 49), (255, 255, 255)],
#         #     [(129, 130, 132), (252, 226, 53)]
#         # ]
#         self.variants =[
#             # [[32, 187, 118], [255, 255, 255]],
#             [[0, 1, 255], [255, 255, 255]]]
#             # [[0, 0, 254], [255, 255, 255]],
#             # [[33, 188, 118], [255, 255, 255]],
#             # [[2, 0, 254], [255, 255, 255]],
#             # [[32, 186, 120], [255, 255, 255]],
#             # [[132, 130, 129], [53, 226, 252]],
#             # [[0, 0, 255], [255, 255, 255]],
#             # [[32, 186, 120], [255, 254, 255]],
#             # [[32, 187, 119], [255, 255, 255]],
#             # [[32, 187, 119], [255, 254, 255]],
#             # [[34, 187, 119], [255, 255, 255]],
#             # [[34, 188, 117], [255, 254, 255]],
#             # [[34, 188, 117], [255, 255, 255]],
#             # [[2, 0, 255], [255, 255, 255]]]
#
#     def check_is_infographic(self, image_path=None, image_url=None,
#                              pim_import=False, tolerance=8):
#         try:
#             if image_url:
#                 try:
#                     response = requests.get(image_url)
#                 except Exception:
#                     return False, image_url
#                 else:
#                     image = np.asarray(bytearray(response.content), dtype=np.uint8)
#                     img = cv2.imdecode(image, cv2.IMREAD_COLOR)
#             elif image_path:
#                 img = cv2.imread(image_path)
#
#             if pim_import:
#                 self.variants = [
#                     [tuple(reversed(color)) for color in pair] for pair in self.variants
#                 ]
#                 self.color_pairs = self.variants
#
#             if not self.color_pairs:
#                 self._collect_infographic_colors()
#
#             height, width, _ = img.shape
#             corners = [
#                 tuple(img[0, 0, :3]),  # Левый верхний угол
#                 tuple(img[0, width-1, :3]),  # Правый верхний угол
#                 tuple(img[height-1, 0, :3]),  # Левый нижний угол
#                 tuple(img[height-1, width-1, :3]),  # Правый нижний угол
#             ]
#
#             middle_top = tuple(img[0, width // 2, :3])  # Середина верхней границы
#             middle_bottom = tuple(img[height - 1, width // 2, :3]) # Середина нижней границы
#
#             for color_pair in self.color_pairs:
#                 upper_colors_count = sum(1 for pixel in [corners[0], corners[1], middle_top] if
#                                          self._is_color(pixel, color_pair[0], tolerance))
#                 down_colors_count = sum(1 for pixel in [corners[2], corners[3], middle_bottom] if
#                                         self._is_color(pixel, color_pair[1], tolerance))
#
#                 if upper_colors_count >= 2 and down_colors_count >= 2:
#                     return True, image_path if image_path else image_url
#
#             return False, image_path if image_path else image_url
#
#         except Exception as e:
#             return False, str(e)
#
#     @staticmethod
#     def _is_color(pixel, color, tolerance):
#         return np.all(np.abs(np.array(pixel) - np.array(color)) <= tolerance)
#
#     @staticmethod
#     def detect_carrera_logo(image_path=None, image_url=None):
#         if image_url:
#             # Загрузка изображения по URL
#             try:
#                 response = requests.get(image_url)
#             except Exception:
#                 return False
#             image = cv2.imdecode(np.array(bytearray(response.content), dtype=np.uint8), cv2.IMREAD_COLOR)
#         elif image_path:
#             # Загрузка изображения из файла
#             image = cv2.imread(image_path)
#             if image is None:
#                 return False
#         else:
#             return False
#
#         height, width, _ = image.shape
#         top_part_height = int(height * 0.11)  # Верхние 12% изображения
#         left_part_width = int(width * 0.63)  # Левая часть изображения (20%)
#         right_part_width = int(width * 0.9)  # Правая часть изображения (20%)
#         top_part = image[0:top_part_height, left_part_width:right_part_width]
#
#         gray_top_part = cv2.cvtColor(top_part, cv2.COLOR_BGR2GRAY)
#         _, black_mask = cv2.threshold(gray_top_part, 50, 255, cv2.THRESH_BINARY_INV)
#         black_pixel_count = cv2.countNonZero(black_mask)
#
#         # Проверка наличия желтого цвета в вырезанной области
#         yellow_pixel_count = 0
#         for row in top_part:
#             for pixel in row:
#                 if (pixel[2] > 240 and pixel[2] < 255) and (pixel[1] > 220 and pixel[1] < 255) and (
#                         pixel[0] > 40 and pixel[0] < 60):
#                     yellow_pixel_count += 1
#
#         corners = [
#             tuple(image[0, 0, :3]),  # Левый верхний угол
#             tuple(image[0, width - 1, :3]),  # Правый верхний угол
#             tuple(image[height - 1, 0, :3]),  # Левый нижний угол
#             tuple(image[height - 1, width - 1, :3]),  # Правый нижний угол
#         ]
#         if not all(corner[0] > 250 and corner[1] > 250 for corner in corners):
#             return False
#
#         # cv2.imshow('Mask', black_mask)
#         # cv2.waitKey(0)
#         # cv2.destroyAllWindows()
#
#         # print(black_pixel_count)
#
#         if black_pixel_count > 1500 and black_pixel_count < 10000 and yellow_pixel_count > 3000:
#             return True
#
#         return False
#
#     @staticmethod
#     def detect_premium_logo(image_path=None, image_url=None):
#         if image_url:
#             # Загрузка изображения по URL
#             try:
#                 response = requests.get(image_url)
#             except Exception:
#                 return False
#             image = cv2.imdecode(np.array(bytearray(response.content), dtype=np.uint8), cv2.IMREAD_COLOR)
#         elif image_path:
#             # Загрузка изображения из файла
#             image = cv2.imread(image_path)
#             if image is None:
#                 return False
#         else:
#             return False
#
#         height, width, _ = image.shape
#         top_part_height = int(height * 0.12)  # Верхние 12% изображения
#         left_part_width = int(width * 0.25)  # Левая часть изображения (20%)
#         right_part_width = width - left_part_width  # Правая часть изображения (20%)
#         top_part = image[0:top_part_height, left_part_width:right_part_width]
#
#         # Преобразование верхней части изображения в HSV для выделения желтого цвета
#         hsv = cv2.cvtColor(top_part, cv2.COLOR_BGR2HSV)
#         # Диапазон желтого цвета в HSV
#         lower_yellow = np.array([20, 140, 140])
#         upper_yellow = np.array([30, 250, 250])
#         # Создание маски для желтого цвета
#         yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
#         # cv2.imshow('Mask', yellow_mask)
#         # cv2.waitKey(0)
#         # cv2.destroyAllWindows()
#         # Подсчет количества белых пикселей (предполагаемый текст)
#         white_pixel_count = cv2.countNonZero(yellow_mask)
#         # Если количество белых пикселей достаточно большое, считаем, что это текст
#         if white_pixel_count > 10000:
#             return True
#
#         return False
#
#     def _collect_infographic_colors(self):
#         dir_path = '/home/vladimir/Downloads'
#
#         # Получаем список файлов изображений
#         image_files = [
#             os.path.join(dir_path, file) for file in os.listdir(dir_path) if file.endswith('.png') or file.endswith('.jpg')
#         ]
#
#         # Разделяем список файлов на части
#         num_threads = 8
#         chunk_size = len(image_files) // num_threads
#         chunks = [image_files[i:i + chunk_size] for i in range(0, len(image_files), chunk_size)]
#
#         t = time.time()
#
#         # Обрабатываем изображения в несколько потоков
#         with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
#             futures = [executor.submit(self._process_colors_chunk, chunk) for chunk in chunks]
#             for future in concurrent.futures.as_completed(futures):
#                 result = future.result()
#                 for pair in result:
#                     if pair not in self.color_pairs:
#                         self.color_pairs.append(pair)
#
#         # print(time.time() - t)
#             # results = [future.result() for future in futures]
#
#         # for result in results:
#         #     for pair in result:
#         #         if pair not in self.color_pairs:
#         #             self.color_pairs.append(pair)
#         self.color_pairs = np.array(self.color_pairs).tolist()
#         # print(self.color_pairs)
#
#     @staticmethod
#     def _process_colors_chunk(chunk):
#         color_pairs = set()
#         for image_file in chunk:
#             img = cv2.imread(image_file)
#             if img is None:
#                 continue
#             height, width, _ = img.shape
#             corners = [
#                 tuple(img[0, 0, :3]),  # Левый верхний угол
#                 tuple(img[height - 1, width - 1, :3]),  # Правый нижний угол
#             ]
#             top_color = corners[0]
#             bottom_color = corners[1]
#             if not top_color == bottom_color:
#                 color_pair = tuple([top_color, bottom_color])
#                 color_pairs.add(color_pair)
#
#         return [list(pair) for pair in color_pairs]
#
# hlp = InfographicImageHelper()

# print(hlp.check_is_infographic(image_url='https://img.mvideo.ru/Big/400422522bb2.jpg', pim_import=True))
# print(hlp.detect_carrera_logo(image_path='/home/vladimir/Downloads/Untitled.jpeg'))
# print(hlp.detect_carrera_logo(image_url='https://img.mvideo.ru/Big/400422522bb2.jpg'))
# print(hlp.check_is_infographic(image_path='/home/vladimir/Downloads/oaqLLIX4PCXrMFdL_20085013bb.jpg'))
# print(hlp.detect_carrera_logo(image_url='https://img.mvideo.ru/Big/400406304bb4.jpg'))
# print(hlp.detect_premium_logo(image_path='/home/vladimir/Downloads/мпремиум/Итог_вертикаль.png'))

#
# img_url = 'https://img.mvideo.ru/Pdb/30075980b.jpg'
# #
# print(hlp.check_is_infographic(image_url=img_url))
# print(hlp.detect_carrera_logo(image_url=img_url))
# print(hlp.detect_premium_logo(image_url=img_url))
#
# img_path = '/home/vladimir/Downloads/Итог_вертикаль_Озон.png'
#
# print(hlp.check_is_infographic(image_path=img_path))
# print(hlp.detect_carrera_logo(image_path=img_path))
# print(hlp.detect_premium_logo(image_path=img_path))


# custom_val = '123 (,)'
# # try:
# custom_val = Decimal(custom_val) if re.search("[.,]", custom_val) or custom_val.isnumeric() else custom_val
# # except Exception:
# #     print(123)
# print(custom_val)

# import xlsxwriter
#
#
# workbook = xlsxwriter.Workbook("/home/vladimir/merge1.xlsx")
# worksheet = workbook.add_worksheet()
# merge_format = workbook.add_format(
#     {
#         "bold": 1,
#         "border": 1,
#         "align": "center",
#         "valign": "vcenter",
#         "fg_color": "yellow",
#     }
# )
# headers_format = workbook.add_format({
#             'bold': True,
#             'border': 1,
#             'border_color': 'black',
#             'bg_color': 'gray',
#             'font_color': 'white',
#             'align': 'center'
#         })
# center_format = workbook.add_format({
#             'border': 1,
#             'border_color': 'black',
#             'text_wrap': True,
#             'align': 'center',
#             'valign': 'vcenter'
#         })
#
# products_data = [{'id': 1, 'name': 'Aaaaaa'}, {'id': 2, 'name': 'BBBBBBBB'},]
#
# headers = ['PIM ID', 'Название товара',]
# for num, header in enumerate(headers, 0):
#     worksheet.merge_range(0, num, 1, num, header, cell_format=headers_format)
#
# heads = ['Тип устройства', 'Режимы фена',]
# worksheet.write_row(0, 2, headers, cell_format=center_format)
#
#
# for row, product_data in enumerate(products_data, 2):
#     worksheet.write_row(row, 0, [product_data['id'], product_data['name']], center_format)
#
# # worksheet.merge_range(0, 0, 1, 1, cell_format=merge_format)
#
# workbook.close()

# from yt_dlp import YoutubeDL
#
# ydl_options = {
#     'format': 'bv[width>=720][height>=720][width<=1920][height<=1920][ext=mp4]+ba[ext=m4a]/mp4',
#     'outtmpl': f'/home/vladimir/Downloads/vid.mp4',
#     'proxy': 'http://aliway:BXLZkh07VAt02bZ1kjL6@45.150.188.135:8111/',
# }
# #
# with YoutubeDL(ydl_options) as ydl:
#     ydl.download(['http://www.youtube.com/watch?v=MlJOKyxjHFo'])
#
a = 'ee efqf eqfqfe'
print(a.split()[-1])