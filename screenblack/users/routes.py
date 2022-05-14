import os
from flask import url_for, render_template, flash, request, redirect, Blueprint, current_app
from flask_login import current_user, login_user, logout_user, login_required
from screenblack import db, bcrypt
from screenblack.models import User, Post
from screenblack.users.forms import RegistrationForm, LoginForm, UpdateAccountForm

from screenblack.users.utils import save_picture

users = Blueprint("users", __name__)   

@users.route("/register", methods=["GET", "POST"])
def register():
  if current_user.is_authenticated:
    return redirect(url_for("main.home"))
  form = RegistrationForm()
  if form.validate_on_submit():
    hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
    user = User(name = form.name.data, username = form.username.data, email = form.email.data, password = hashed_password)
    db.session.add(user)
    db.session.commit()
    flash(f"Account created!", "success")
    return redirect(url_for("users.login"))
  return render_template("register.html", title = "Sign Up", form = form)


@users.route("/login", methods=["GET", "POST"])
def login():
  if current_user.is_authenticated:
    return redirect(url_for("main.home"))
  form = LoginForm()
  if form.validate_on_submit():
    user = User.query.filter_by(email = form.email.data).first()
    if user and bcrypt.check_password_hash(user.password, form.password.data):
      login_user(user, remember=form.remember.data)
      next_page = request.args.get("next")
      return redirect(next_page) if next_page else redirect(url_for("main.home"))
    else:
      flash("Login Unsuccessful", "danger")
  return render_template("login.html", title = "Login", form = form)

@users.route("/logout")
def logout():
  logout_user()
  return redirect(url_for("main.home"))


@users.route("/account", methods=['GET', 'POST'])
@login_required
def account():

  form = UpdateAccountForm()

  if form.validate_on_submit():

    if form.picture.data:
      old_pic = current_user.picture
      pic_file_name = save_picture(form.picture.data)
      current_user.picture = pic_file_name
      if old_pic != 'default.jpg':
        try:
          os.remove(os.path.join(current_app.root_path, 'static/profilepics', old_pic))
        except:
          pass
    
    current_user.name = form.name.data
    current_user.username = form.username.data
    current_user.email = form.email.data
    db.session.commit()
    flash("Your details have been Updated!", "success")
    return redirect(url_for("users.account"))
  elif request.method =="GET":
    form.name.data = current_user.name
    form.username.data = current_user.username
    form.email.data = current_user.email

  picture = url_for('static', filename='profilepics/' + current_user.picture)
  return render_template('account.html', title='Account', picture=picture, form=form)

@users.route("/user/<string:username>")
def user_about(username):
  page = request.args.get("page", default=1, type=int)
  user = User.query.filter_by(username=username).first_or_404()
  posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page = page, per_page=5)
  return render_template("user_about.html", user = user, posts = posts, title = username)
