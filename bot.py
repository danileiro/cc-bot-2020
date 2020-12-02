import re
import time
import telebot
from telebot import types
import secrets
from random import randint
from utils import getAddress
import model
TOKEN = "API-KEY-HERE"

usuarios = []
passoAtual = {}
dadosUsuario = {}
commands = {  
    'start': 'Conhecer o bot e iniciar o atendimento',
    'help': 'Ver os comandos disponíveis',
    'pedido': 'Faca um novo pedido em poucos passos ou consulte o status do seu pedido',
}
opcoes = [
    'Porção de Batatas + Suco de Laranja - R$21,60',
    'Hamburguer grelhado + Coca-Cola - R$25,90',
    'ChesseBurguer Especial - R$28,30',
    'Lanche Vegetariano + Água - R$32,90',
    'HotDog Prensado - R$19,90'
]
pedidoSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True)
pedidoSelect.add('Novo pedido', 'Status pedido')

hideBoard = types.ReplyKeyboardRemove()


def getOpcoes():
    textOpcoes = 'Legal! Me diz qual opção você deseja:\n'
    for i in range(len(opcoes)):
        textOpcoes += str(i+1) + ": "
        textOpcoes += opcoes[i] + "\n"
    return textOpcoes

def get_passo_usuario(uid):
    if uid in passoAtual:
        return passoAtual[uid]
    else:
        usuarios.append(uid)
        passoAtual[uid] = 0
        print("Novo usuário detectado")
        return 0

def set_passo_usuario(uid):
    if not uid in dadosUsuario:
        dadosUsuario[uid] = {'user_id': uid}
    return

# Saída para console
def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            print(str(m.chat.first_name) +
                  " [" + str(m.chat.id) + "]: " + m.text)

bot = telebot.TeleBot(TOKEN)
bot.set_update_listener(listener)

# rota para o comando "/start"
@bot.message_handler(commands=['start'])
def command_start(m):
    cid = m.chat.id
    if cid not in usuarios:
        usuarios.append(cid)
        passoAtual[cid] = 0
        dadosUsuario[cid] = {'user_id': cid}
        bot.send_message(
            cid, "Olá, eu sou um bot para o projeto integrador...")
        bot.send_message(
            cid, "Posso simular o atendimento para geração ou consulta de um pedido!")
        command_help(m)
    else:
        bot.send_message(
            cid, "Olá, que bom falar com você novamente!\nDigite /help se precisar de ajuda.")

# rota para o comando "/help" 
@bot.message_handler(commands=['help'])
def command_help(m):
    cid = m.chat.id
    help_text = "Posso te ajudar com os seguintes comandos: \n"
    for key in commands:
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)

# rota para o comando "/pedido" 
@bot.message_handler(commands=['pedido'])
def fazerPedido(m):
    cid = m.chat.id
    typing(3, m)
    bot.send_message(cid, "O que deseja fazer?",
                     reply_markup=pedidoSelect)
    set_passo_usuario(cid)
    passoAtual[cid] = 'pedido'

# caso o passo atual do usuário seja "pedido", mostrar opções
@bot.message_handler(func=lambda message: get_passo_usuario(message.chat.id) == 'pedido')
def selecionarPedido(m):
    cid = m.chat.id
    text = m.text
    dadosUsuario[cid]['opcao'] = None
    bot.send_chat_action(cid, 'typing')
    if text == 'Novo pedido':
        passoAtual[cid] = 0
        bot.send_chat_action(cid, 'typing')
        bot.reply_to(m, getOpcoes())
        bot.send_chat_action(cid, 'typing')
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        for k in range(len(opcoes)):
            markup.add(str(k+1))
        #markup.add('2', '3', '4', '5')
        msg = bot.send_message(
            cid,
            'Selecione uma opção: ',
            reply_markup=markup,
        )
        bot.register_next_step_handler(msg, informarCep)
    elif text == 'Status pedido':
        passoAtual[cid] = 0
        msg = bot.send_message(
            cid,
            'Digite o número do pedido.'
        )
        bot.register_next_step_handler(msg, buscarNumPedido)
    else:
        bot.send_message(cid, "Por favor, use o teclado predefinido!")
        bot.send_message(cid, "Tente novamente.")

def informarCep(m):
    try:
        cid = m.chat.id
        op = int(m.text)
        if (op > len(opcoes)):
            raise Exception("Opção inválida")
        if (dadosUsuario[cid]['opcao'] == None):
            dadosUsuario[cid]['opcao'] = op-1
        typing(4, m)
        bot.reply_to(m, "Ok")
        typing(2, m)
        msg = bot.send_message(
            cid,
            'Digite seu CEP para entrega: XXXXX-XXX ',
        )
        bot.register_next_step_handler(msg, confirmarCep)
    except Exception as e:
        print(e)
        bot.reply_to(m, 'Erro ao validar resposta, por favor digite /pedido e tente novamente! ')
        bot.send_message(cid, "Por favor, use o teclado predefinido!")

def confirmarCep(m):
    try:
        cid = m.chat.id
        form_option = m.text
        if (form_option == '/start'):
            command_start(m)
        typing(4, m)
        bot.reply_to(m, "Buscando endereço...")
        bot.send_chat_action(m.chat.id, 'typing')
        address = getAddress(re.search('\d{5}-?\d{3}', form_option).group())
        if (address == 'False'):
            raise Exception('error')
        address.pop('cidade_info')
        address.pop('estado_info')
        dadosUsuario[cid]['address'] = address
        msg = f"""
        Esse endereço está correto?

        {address.get('logradouro')}
        {address.get('bairro')}
        {address.get('cidade')}
        {address.get('estado')}"""
        bot.send_message(cid, msg)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Sim', 'Nao')
        msg = bot.send_message(
            cid,
            'Selecione uma opção: ',
            reply_markup=markup,
        )
        bot.register_next_step_handler(msg, getNumEndereco)
    except Exception as ex:
        print(ex)
        bot.reply_to(
            m, "Desculpe! Não consegui encontrar esse endereço, tente novamente ou digite outro CEP.")
        typing(2, m)
        msg = bot.send_message(
            cid,
            'Digite seu CEP para entrega: XXXXX-XXX ',
        )
        bot.register_next_step_handler(msg, confirmarCep)

def getNumEndereco(m):
    try:
        cid = m.chat.id
        form_option = m.text
        if (form_option == 'Sim' or form_option == 'sim'):
            typing(2, m)
            bot.reply_to(m, 'Ok!')
            msg = bot.send_message(
                cid,
                'Informe o número da residência e complemento se houver.',
            )
            bot.register_next_step_handler(msg, retornarPedido)
        elif (form_option == 'Nao' or form_option == 'nao'):
            informarCep(m)
        else:
            bot.send_message(cid, "Desculpe, não entendi")
    except Exception as ex:
        print(ex)

def retornarPedido(m):
    cid = m.chat.id
    form_option = m.text
    dadosUsuario[cid]['numCasa'] = form_option
    if not dadosUsuario[cid].get('numPedido'):
        dadosUsuario[cid]['numPedido'] = int(secrets.token_hex(4), 16)
    dadosUsuario[cid]['entrega'] = randint(5, 13)
    typing(2, m)
    model.savedadosUsuario({dadosUsuario[cid].get('numPedido'): dadosUsuario[cid]})
    msg = bot.send_message(
        cid,
        'Pedido realizado!\n' +
        'Prazo de entrega: '+str(dadosUsuario[cid]['entrega']) +
        ' dias.\nEste é o número do seu pedido:\n\n'+str(dadosUsuario[cid]['numPedido']) +
        '\n' + opcoes[int(dadosUsuario[cid]['opcao'])] +
        '\n\nCom ele você pode acompanhar o status da entrega usando o comando /pedido.'
    )
    del dadosUsuario[cid]

def buscarNumPedido(m):
    try:
        cid = m.chat.id
        form_option = m.text
        data = model.getdadosUsuario(re.search('[0-9]+', form_option).group())
        dadosUsuario[cid] = data
        bot.send_chat_action(cid, 'typing')
        pedido = 'Pedido: '+str(data.get('numPedido'))+'\nProduto: '+opcoes[int(data.get('opcao'))]+'\nEndereço: \n'+data.get('address').get('logradouro')+', '+data.get('numCasa')+'\nCEP: '+data.get('address').get(
            'cep')+'\n'+data.get('address').get('bairro')+'\n'+data.get('address').get('cidade')+' - '+data.get('address').get('estado')+'\n\nPrevisto para entrega em '+str(data.get('entrega'))+' dias.'
        bot.send_message(
            cid,
            pedido
        )
        options = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        options.add('Editar pedido', 'Cancelar pedido')
        msg = bot.send_message(
            cid, 'O que deseja fazer?', reply_markup=options)
        bot.register_next_step_handler(msg, statusPedido)
    except Exception as ex:
        print(ex)
        bot.send_message(
            cid,
            'Desculpe, nao encontrei esse pedido. Confirme se o número esta correto'
        )
        del dadosUsuario[cid]
        fazerPedido(m)

def statusPedido(m):
    cid = m.chat.id
    form_option = m.text

    if form_option == 'Editar pedido':
        dadosUsuario[cid]['opcao'] = None
        bot.send_chat_action(cid, 'typing')
        bot.reply_to(m, getOpcoes())
        bot.send_chat_action(cid, 'typing')
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('1', '2', '3', '4', '5')
        msg = bot.send_message(
            cid,
            'Selecione uma opção: ',
            reply_markup=markup,
        )
        bot.register_next_step_handler(msg, informarCep)
    elif form_option == 'Cancelar pedido':
        num = dadosUsuario[cid].get('numPedido')
        model.deletedadosUsuario(num)
        bot.send_message(
            cid,
            f'Pedido {num} cancelado!\nDigite /pedido para fazer um novo pedido.'
        )
    else:
        bot.send_message(cid, "Por favor, use o teclado predefinido!")
        bot.send_message(cid, "Tente novamente.")

# Rota padrão para mensagens comuns
@bot.message_handler(func=lambda message: True, content_types=['text'])
def command_default(m):
    bot.send_message(m.chat.id, "Não sei o que fazer com \"" +
                     m.text + "\".\nConsulte os comandos com /help")

def typing(qtd, message):
    for n in range(qtd):
        bot.send_chat_action(message.chat.id, 'typing')

bot.polling(none_stop=True)
