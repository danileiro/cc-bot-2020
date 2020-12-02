import requests

def getAddress(cep):
    url = f"https://api.postmon.com.br/v1/cep/{cep}"
    r = requests.get(url)
    if (r.status_code == 200):
        return r.json()
    return 'False'

