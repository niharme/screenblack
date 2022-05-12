import os
import secrets
from PIL import Image
from flask import url_for, render_template, redirect, flash, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from screenblack import app, db, bcrypt
from screenblack.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from screenblack.models import User, Post


@app.route("/")
@app.route("/home")
def home():
  posts = Post.query.all()
  return render_template("home.html", posts = posts)


@app.route("/about")
def about():
  return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register():
  if current_user.is_authenticated:
    return redirect(url_for("home"))
  form = RegistrationForm()
  if form.validate_on_submit():
    hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
    user = User(username = form.username.data, email = form.email.data, password = hashed_password)
    db.session.add(user)
    db.session.commit()
    flash(f"Account created, you can now login", "success")
    return redirect(url_for("login"))
  return render_template("register.html", title = "Sign Up", form = form)


@app.route("/login", methods=["GET", "POST"])
def login():
  if current_user.is_authenticated:
    return redirect(url_for("home"))
  form = LoginForm()
  if form.validate_on_submit():
    user = User.query.filter_by(email = form.email.data).first()
    if user and bcrypt.check_password_hash(user.password, form.password.data):
      login_user(user, remember=form.remember.data)
      next_page = request.args.get("next")
      return redirect(next_page) if next_page else redirect(url_for("home"))
    else:
      flash("Login Unsuccessful", "danger")
  return render_template("login.html", title = "Login", form = form)

@app.route("/logout")
def logout():
  logout_user()
  return redirect(url_for("home"))


# // todo:crop image

def crop_center(pil_img, crop_width, crop_height):
  img_width, img_height = pil_img.size
  return pil_img.crop(((img_width - crop_width) // 2, (img_height - crop_height) // 2, (img_width + crop_width) // 2, (img_height + crop_height) // 2))


def crop_max_square(pil_img):
  return crop_center(pil_img, min(pil_img.size), min(pil_img.size))


###

def save_picture(form_picture):
  ranodm_hex = secrets.token_hex(8)
  _, file_ext = os.path.splitext(form_picture.filename)
  pic_file_name = ranodm_hex + file_ext
  pic_path = os.path.join(app.root_path, "static/profilepics", pic_file_name)

  i = Image.open(form_picture)
  i = crop_max_square(i)


  output_size = (125, 125)
  i.thumbnail(output_size)


  i.save(pic_path)

  return pic_file_name



@app.route("/account", methods=['GET', 'POST'])
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
          os.remove(os.path.join(app.root_path, 'static/profilepics', old_pic))
        except:
          pass

    current_user.username = form.username.data
    current_user.email = form.email.data
    db.session.commit()
    flash("Your details have been Updated!", "success")
    return redirect(url_for("account"))
  elif request.method =="GET":
    form.username.data = current_user.username
    form.email.data = current_user.email

  picture = url_for('static', filename='profilepics/' + current_user.picture)
  return render_template('account.html', title='Account', picture=picture, form=form)


@app.route("/post/new", methods=["GET", "POST"])
@login_required
def create_post():
  form = PostForm()
  if form.validate_on_submit():
    post = Post(title = form.title.data, content = form.content.data, author = current_user)
    db.session.add(post)
    db.session.commit()
    flash("Your post has been created.", "success")
    return redirect(url_for("home"))
  return render_template("create_update_post.html", title="New Post", form=form, legend="New Post")

@app.route("/post/<int:post_id>")
def post(post_id):
  post = Post.query.get_or_404(post_id)
  return render_template("post.html", post=post, title=post.title)



@app.route("/post/<int:post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
  post = Post.query.get_or_404(post_id)
  form = PostForm()
  if post.author != current_user:
    abort(403)
  if form.validate_on_submit():
    post.title = form.title.data
    post.content = form.content.data
    db.session.commit()
    flash("Your post has been updated!", "success")
    return redirect(url_for("post", post_id=post.id))

  elif request.method == "GET":
    form.title.data = post.title
    form.content.data = post.content


  return render_template("create_update_post.html", post=post, title=post.title, form=form, legend="Update Post")



@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
  post = Post.query.get_or_404(post_id)
  if post.author != current_user:
    abort(403)
  
  db.session.delete(post)
  db.session.commit()

  flash("Post Deleted!", "success")
  return redirect(url_for("home"))
