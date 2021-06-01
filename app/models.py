from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5
from time import time
import jwt
from flask import current_app
from app.search import add_to_index, remove_from_index, query_index


followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))


class User(UserMixin, db.Model):
    """用户表"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship('User', secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """校验密码"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    def avatar(self, size):
        """生成头像链接"""
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        # 参数d: identicon, monsterid
        return 'https://gravatar.zeruns.tech/avatar/{}?d=identicon&s={}'.format(
            digest, size
        )

    def is_following(self, user):
        """A是否关注了B"""
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def follow(self, user):
        """A关注B"""
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        """A取消关注B"""
        if self.is_following(user):
            self.followed.remove(user)

    def get_reset_password_token(self, expires_in=600):
        """生成重置密码所需的令牌"""
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in},
                           c.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        """验证令牌是是否有效，有效返回用户"""
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def followed_posts(self):
        """查看已关注用户的动态"""
        followed = Post.query.join(followers,
                                   (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.time_stamp.desc())


class SearchableMixin:
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        # when = []
        # for i in range(len(ids)):
        #     when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(cls.id.desc()), total
        # return cls.query.filter(cls.id.in_(ids)).order_by(db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': [obj for obj in session.new if isinstance(obj, cls)],
            'update': [obj for obj in session.dirty if isinstance(obj, cls)],
            'delete': [obj for obj in session.deleted if isinstance(obj, cls)]
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            add_to_index(cls.__tablename__, obj)
        for obj in session._changes['update']:
            add_to_index(cls.__tablename__, obj)
        for obj in session._changes['delete']:
            remove_from_index(cls.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


class Post(SearchableMixin, db.Model):
    """用户动态表"""

    __searchable__ = ['body']

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    time_stamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return f'<Post {self.body}>'


db.event.listen(db.session, 'before_commit', Post.before_commit)
db.event.listen(db.session, 'after_commit', Post.after_commit)


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


