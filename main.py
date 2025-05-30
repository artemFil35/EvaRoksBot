from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = '7561603783:AAEaqUMoxip70_rrCZae-0AbpcqxmZLA04w'
BOT_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'
BITRIX_URL = 'https://tdroks.bitrix24.ru/rest/1/bf7o1k7xogfxn3c1/crm.deal.add.json'
DADATA_TOKEN = '5c7912fc8d82c25eaff25d91a0f87a93076655aa'

USD_RATE = 85
DELIVERY_RATE = 1.5

def send_telegram(chat_id, text):
    requests.post(f'{BOT_URL}/sendMessage', json={'chat_id': chat_id, 'text': text})

def check_inn(inn):
    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {DADATA_TOKEN}"
    }
    data = { "query": inn }
    r = requests.post(url, json=data, headers=headers)
    res = r.json()
    if res.get('suggestions'):
        org = res['suggestions'][0]['data']
        name = org['name']['short_with_opf']
        status = org['state']['status']
        address = org['address']['value']
        return name, address, status
    else:
        return None, None, None

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if 'message' not in data:
        return 'ok'
    chat_id = data['message']['chat']['id']
    text = data['message'].get('text', '').strip()

    if text.startswith('/start'):
        send_telegram(chat_id, "👋 Введи ГОСТ, ISO, размеры или ИНН компании:")
        return 'ok'

    if text.isdigit() and (9 <= len(text) <= 12):
        name, address, status = check_inn(text)
        if name:
            message = f"✅ Найдено:\n🏢 {name}\n📍 {address}\n📌 Статус: {status}"
            send_telegram(chat_id, message)
            payload = {
                'fields': {
                    'TITLE': f'Запрос от {name}',
                    'COMMENTS': f'ИНН: {text}\nНазвание: {name}\nАдрес: {address}\nСтатус: {status}',
                    'STAGE_ID': 'NEW',
                    'CATEGORY_ID': 0,
                    'SOURCE_ID': 'WEB',
                    'SOURCE_DESCRIPTION': 'Telegram Bot EvaRoksBot'
                }
            }
            requests.post(BITRIX_URL, data=payload)
        else:
            send_telegram(chat_id, "❌ Компания по этому ИНН не найдена.")
        return 'ok'

    podshipnik = text
    ves = 0.3
    dostavka = round(ves * DELIVERY_RATE * USD_RATE, 2)
    msg = f"🔍 Подшипник: {podshipnik}\n⚖️ Вес: {ves} кг\n🚛 Доставка: {dostavka} ₽\n📩 Укажи ИНН или e-mail"
    send_telegram(chat_id, msg)
    payload = {
        'fields': {
            'TITLE': f'Запрос подшипника {podshipnik}',
            'COMMENTS': f'Подшипник: {podshipnik}\nВес: {ves} кг\nДоставка: {dostavka} ₽',
            'STAGE_ID': 'NEW',
            'CATEGORY_ID': 0,
            'SOURCE_ID': 'WEB',
            'SOURCE_DESCRIPTION': 'Telegram Bot EvaRoksBot'
        }
    }
    requests.post(BITRIX_URL, data=payload)
    return 'ok'
