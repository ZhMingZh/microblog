from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app
from app import db
from app.main.forms import EditProfileForm, PostForm, SearchForm
from flask_login import current_user, login_required
from app.models import User, Post
from datetime import datetime
from flask_babel import _, get_locale
from langdetect import detect
from app.translate import translate
from app.main import bp


@bp.before_request
def before_request():
    """记录用户每次最后的访问时间"""
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    # 返回给定请求的语言和语言环境,并添加到g对象
    lang = str(get_locale())
    g.locale = 'zh-CN' if lang == 'zh' else lang


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    """首页"""
    form = PostForm()
    if form.validate_on_submit():
        language = detect(form.post.data)[:2]  # 中文识别为zh
        if len(form.post.data) < 8:
            language = ''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title=_('Home Page'), posts=posts.items, form=form,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>')
def user(username):
    """个人主页"""
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.time_stamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


# 更改重复的名字会报错;表单更改了验证还是一样报错;已修复
@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑个人界面"""
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)


@bp.route('/follow/<username>')
@login_required
def follow(username):
    """关注其他用户"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot follow yourself'))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    """取消关注其他用户"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself'))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('main.user', username=username))


@bp.route('/explore')
@login_required
def explore():
    """展示最新的post"""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.time_stamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False
    )
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title=_('Explore'), posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    # print(f'routes:{request.form["source_language"]}')
    return jsonify({'text': translate(
        request.form['text'],
        request.form['source_language'],
        request.form['dest_language'][:2])})  # zh-CN


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    # print(page, total, current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)