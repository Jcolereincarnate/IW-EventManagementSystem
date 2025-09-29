import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw
import os
from django.conf import settings
'''
def generate_code(data, filename):
    qr = qrcode.make(data)
    qr_dir = os.path.join(settings.MEDIA_ROOT, "qrcodes")
    os.makedirs(qr_dir, exist_ok=True)
    qr_path = os.path.join(qr_dir, filename)
    qr.save(qr_path)
    return f"qrcodes/{filename}"
'''



def generate_code(data, filename, logo_path=None):
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        #resizing the logo to fit the center of QR code
        qr_width, qr_height = qr_img.size
        logo_size = qr_width // 4
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

        #Creating a background for the logo so it fits perfectly into the QR code
        logo_bg = Image.new("RGBA", (logo_size, logo_size), (255, 255, 255, 0))
        mask = Image.new("L", (logo_size, logo_size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, logo_size, logo_size), fill=255)  # circle shape
        logo_bg.paste((153, 255, 255, 255), (0, 0), mask)  #PIL uses RGBA, so rememeber that whenever you alter the color values
        logo_bg.paste(logo, (0, 0), logo)  

        #using the width and height of the QR code to position the logo at the center
        pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
        qr_img.paste(logo_bg, pos, logo_bg)
    
    qr_dir = os.path.join(settings.MEDIA_ROOT, "qrcodes")
    os.makedirs(qr_dir, exist_ok=True)
    qr_path = os.path.join(qr_dir, filename)
    qr_img.save(qr_path, format="PNG")

    return f"qrcodes/{filename}"