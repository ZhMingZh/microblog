from flask import render_template, flash, redirect, url_for, request, g, jsonify
from app import app, db
from older.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post
from werkzeug.urls import url_parse
from datetime import datetime
from app.email import send_reset_password_email
from flask_babel import _, get_locale
from langdetect import detect
from app.translate import translate


@app.before_request
def before_request():
    """记录用户每次最后的访问时间"""
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    # 返回给定请求的语言和语言环境,并添加到g对象
    lang = str(get_locale())
    g.locale = 'zh-CN' if lang == 'zh' else lang


@app.route('/', methods=['GET', 'POST'])
@app.route('/index',  methods=['GET', 'POST'])
@login_required
def index():
    """首页"""
    form = PostForm()
    if form.validate_on_submit():
        language = detect(form.post.data)[:2]  # 中文识别为zh
        print(language)
        # if language == '' or len(language) > 5:
        #     language = ''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title=_('Home Page'), posts=posts.items, form=form,
                           next_url=next_url, prev_url=prev_url)
   

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登入"""
    # 用户已登陆直接跳转到首页
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        # 查询用户是否存在和校验密码是否正确
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title=_('Sign In'), form=form)


@app.route('/logout')
def logout():
    """登出"""
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('login'))
    return render_template('register.html', title=_('Register'), form=form)


@app.route('/user/<username>')
def user(username):
    """个人主页"""
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.time_stamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


# 更改重复的名字会报错;表单更改了验证还是一样报错;已修复
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑个人界面"""
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    """关注其他用户"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot follow yourself'))
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    """取消关注其他用户"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself'))
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('user', username=username))


@app.route('/explore')
@login_required
def explore():
    """展示最新的post"""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.time_stamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False
    )
    next_url = url_for('explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title=_('Explore'), posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """重置密码的请求"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_password_email(user)
        flash(_('Check the email for the instructions to reset your password.'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title=_('Reset Password'), form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """重置密码"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/translate', methods=['POST'])
@login_required
def translate_text():
    print(f'routes:{request.form["source_language"]}')
    return jsonify({'text': translate(
        request.form['text'],
        request.form['source_language'],
        request.form['dest_language'][:2])})   # zh-CN