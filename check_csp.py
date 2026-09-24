import urllib.request

try:
    response = urllib.request.urlopen('https://meet.google.com/')
    print(response.headers)
except Exception as e:
    print(e.headers)
