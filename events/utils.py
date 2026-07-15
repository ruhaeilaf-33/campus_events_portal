from io import BytesIO
from django.http import FileResponse
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import ImageReader
import os


def generate_certificate(registration):
    buffer = BytesIO()

    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # ✅ FIX 1: Use Django's BASE_DIR to build a portable path
    template_path = os.path.join(
        settings.BASE_DIR,
        "static",
        "images",
        "certificate_template.png"
    )

    # ✅ FIX 2: Check the file actually exists before drawing
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Certificate template not found at: {template_path}"
        )

    p.drawImage(ImageReader(template_path), 0, 0, width=width, height=height)

    p.setFont("Times-BoldItalic", 18)
    p.drawCentredString(width / 2, 278, registration.full_name)

    p.setFont("Times-BoldItalic", 15)
    p.drawCentredString(width / 2 + 45, 252, registration.event.title)

    p.setFont("Times-BoldItalic", 13)
    p.drawString(195, 220, str(registration.event.date))

    p.setFont("Helvetica-Bold", 10)
    p.drawString(90, 138, str(registration.certificate_id))

    p.save()
    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename="SJB_Participation_Certificate.pdf"
    )