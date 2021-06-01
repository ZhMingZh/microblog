import json
import requests
from flask_babel import _
from flask import current_app
from time import time
from hashlib import md5


translate_url = 'http://api.fanyi.baidu.com/api/trans/vip/translate'


def translate(text, source_language, dest_language):

    if ('BDKEY' not in current_app.config or not current_app.config['BDKEY']) or \
            ('BDAPPID' not in current_app.config or not current_app.config['BDAPPID']):
        return _('Error: the translation service is not configured.')
    salt = str(int(time()))
    string = current_app.config['BDAPPID'] + text + salt + current_app.config['BDKEY']
    # string = '2015063000000001apple143566028812345678'
    sign = md5(string.encode('utf-8')).hexdigest()
    # 处理识别语言和翻译语言之间国家语言代码不同的问题
    lang = {'ja': 'jp'}
    source_language = lang.get(source_language) or source_language
    # print(source_language, dest_language, text)
    args = {
        'q': text,
        'from': source_language,
        'to': dest_language,
        'appid': current_app.config['BDAPPID'],
        'salt': salt,
        'sign': sign
    }
    result = requests.get(translate_url, params=args).json()
    if 'error_code' in result:
        return _('Error: %(error_msg)s', error_msg=result['error_msg'])

    return result['trans_result'][0]['dst']





