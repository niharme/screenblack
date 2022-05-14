import os
import secrets
from PIL import Image
from flask import current_app


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
  pic_path = os.path.join(current_app.root_path, "static/profilepics", pic_file_name)

  i = Image.open(form_picture)
  i = crop_max_square(i)


  output_size = (128, 128)
  i.thumbnail(output_size)


  i.save(pic_path)

  return pic_file_name

