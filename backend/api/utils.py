from collections import namedtuple
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from api.constants import (
    TITLE,
    HEADER_TEXT,
    FOOTER_TEXT,
    FONT_FAMILY,
    REGISTER_FONT_URL,
    FONT_SIZE,
    TEXT_CANVAS_H,
    TEXT_CANVAS,
    TEXT_COLOR,
    BOX_COLOR,
    VALIGN,
    ALIGN,
    TOPPADDING,
    BOTTOMPADDING,
    LEFTPADDING,
    FONTNAME,
    FONTSIZE,
    LINEBELOW_COLOR,
    LINEBELOW,
    BACKGROUND_COLOR,
    GRID_COLOR,
    GRID,
    DATA_COLUMN1,
    DATA_COLUMN2,
)


def ingredients_list(recipe_list):
    ingredients = {}
    for recipe in recipe_list:
        for _ in recipe.recipe_ingredients.select_related('ingredient').all():
            key = (_.ingredient.name, _.ingredient.measurement_unit)
            if key not in ingredients:
                ingredients[key] = 0
            ingredients[key] += _.amount

    return [ShoppingListItem(name, amount, measurement_unit)
            for ((name, measurement_unit), amount) in ingredients.items()]


def pdf_shopping_list(shopping_list, user):

    def header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(FONT_FAMILY, FONT_SIZE)
        w, h = doc.pagesize
        canvas.drawString(inch, h - TEXT_CANVAS_H * inch, HEADER_TEXT)
        canvas.drawString(inch, TEXT_CANVAS * inch, FOOTER_TEXT)
        canvas.restoreState()

    pdfmetrics.registerFont(
        TTFont(FONT_FAMILY, REGISTER_FONT_URL)
    )
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        title=TITLE
    )

    data = [
        [DATA_COLUMN1, DATA_COLUMN2]
    ]

    for ingredient in shopping_list:
        data.append([ingredient[0], f'{ingredient[1]} {ingredient[2]}'])

    table = Table(data)
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (-1, 0), (0, 0), TEXT_COLOR),
        ("BOX", (0, 0), (-1, -1), 0, BOX_COLOR),
        ("VALIGN", (0, 0), (-1, -1), VALIGN),
        ("ALIGN", (0, 0), (-1, -1), ALIGN),
        ("TOPPADDING", (0, 0), (-1, -1), TOPPADDING),
        ("BOTTOMPADDING", (0, 0), (-1, -1), BOTTOMPADDING),
        ("LEFTPADDING", (0, 0), (-1, -1), LEFTPADDING),
        ('FONTNAME', (0, 0), (-1, -1), FONTNAME),
        ("FONTSIZE", (0, 0), (-1, -1), FONTSIZE),
        ("LINEBELOW", (0, -1), (-1, -1), LINEBELOW, LINEBELOW_COLOR),
        ('BACKGROUND', (0, 1), (-1, -1), BACKGROUND_COLOR),
        ('GRID', (0, 0), (-1, -1), GRID, GRID_COLOR)
    ]))

    doc.build(
        [table],
        onFirstPage=header_footer,
        onLaterPages=header_footer
    )
    buffer.seek(0)

    return buffer


ShoppingListItem = namedtuple(
    'ShoppingListItem',
    ['name', 'amount', 'measurement_unit']
)
