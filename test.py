# import requests
#
#
# file = {
#         'image_file': ("/home/vladimir/python/remote_manager/",
#                       open("/home/vladimir/python/remote_manager/9.jpeg", 'rb'),
#                       'image/jpg')
# }
#
# response = requests.post(url='https://sdk.photoroom.com/v1/segment',
#                          headers={'x-api-key': '6c56c73288eb8c78f05a5487448a948fc123a290'},
#                          files=file,
#                          stream=True)
#
# print(response.status_code)
#
# print(response.headers.get('x-uncertainty-score'))
#
# if response.ok:
#     with open("/home/vladimir/python/remote_manager/RESULT.jpg", 'wb') as f:
#         for image_bytes in response.iter_content(1024):
#             f.write(image_bytes)

a = -1

print(float(a))

if float(a) == -1:
    print(22)