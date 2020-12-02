import json
import os

def savedadosUsuario(dadosUsuario):
    with open('db/data.json', 'r+') as jsonFile:
        data = json.load(jsonFile)
        data.update(dadosUsuario)
        jsonFile.seek(0)
        json.dump(data, jsonFile)
        data = None

def getdadosUsuario(numPedido):
    with open('db/data.json', 'r') as jsonFile:
        data = json.load(jsonFile)
        if str(numPedido) in data:
            return data[numPedido]
        raise Exception('Pedido nao encontrado')

def deletedadosUsuario(numPedido):
    with open('db/data.json', 'r') as jsonFile:
        data = json.load(jsonFile)
    if str(numPedido) in data:
        del data[str(numPedido)]
    else:
        print(data)
        data = None
        return    
    with open('db/data.json', 'w') as jsonFile:
        json.dump(data, jsonFile)
        data = None
        