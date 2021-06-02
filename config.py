import os
from dotenv import load_dotenv


basedir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(basedir, '.flaskenv'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guss'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 邮件服务器相关设置
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['z17328841951@163.com']
    # 每页显示的数据
    POSTS_PER_PAGE = 10
    # 支持的语言
    LANGUAGES = ['zh', 'en', 'es']
    BDAPPID = os.environ.get('BDAPPID')
    BDKEY = os.environ.get('BDKEY')

