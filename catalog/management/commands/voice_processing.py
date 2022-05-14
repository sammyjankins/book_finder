import json
import os

import requests

from book_finder import settings

URL_REC = 'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize'
URL_SYNTH = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
YA_TOKEN_REFRESH_URL = 'https://iam.api.cloud.yandex.net/iam/v1/tokens'


def recognize(file_path):
    with open(file_path, "rb") as f:
        data_sound = f.read()
    os.remove(file_path)
    headers = {'Authorization': f'Bearer {create_token(os.environ.get("YANDEX_OAUTH"))[0]}'}

    params = {
        'lang': 'ru-RU',
        'folderId': os.environ.get('YANDEX_FOLDER_ID'),
        'sampleRateHertz': 48000,
    }

    response = requests.post(URL_REC, params=params, headers=headers, data=data_sound)
    decode_resp = response.content.decode('UTF-8')
    text = json.loads(decode_resp)

    return text


def synthesize(text, file_path):
    headers = {'Authorization': f'Bearer {create_token(os.environ.get("YANDEX_OAUTH"))[0]}'}
    params = {
        'text': text,
        'lang': 'ru-RU',
        'folderId': os.environ.get('YANDEX_FOLDER_ID'),
        'voice': 'ermil',
    }

    response = requests.post(URL_SYNTH, params=params, headers=headers)
    with open(file_path, mode='wb') as file:
        file.write(response.content)


def create_token(oauth_token):
    params = {'yandexPassportOauthToken': oauth_token}
    response = requests.post(YA_TOKEN_REFRESH_URL, params=params)
    decode_response = response.content.decode('UTF-8')
    text = json.loads(decode_response)
    iam_token = text.get('iamToken')
    expires_iam_token = text.get('expiresAt')

    return iam_token, expires_iam_token


if __name__ == '__main__':
    answer_path = os.path.join(settings.BASE_DIR, 'answer.ogg')
    synthesize(
        'Теперь все работает. Оказывается я использовал неверный фолдер айди, так как скопировал его не из того места.'
        'Верный фолдер айди я выяснил в процессе настройки в командной строке по команде уай си инит. '
        'Спасибо за помощь.',
        answer_path)
    print(recognize(answer_path))
