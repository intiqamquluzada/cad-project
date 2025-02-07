import os
from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.conf import settings
import ezdxf
import pandas as pd

def generate_dxf(path_of_file):
    quyular = pd.read_excel(path_of_file)
    laylar = pd.read_excel(path_of_file, sheet_name="Sheet2")

    def add_text(msp, text, position, height=2, bold=False, font="Arial Unicode MS"):
        mtext = msp.add_mtext(text, dxfattribs={"char_height": height, "style": font})
        mtext.set_location(position)

        if bold:
            mtext.dxf.style = "Bold"

    def add_line(msp, start, end, color=7, layer=None):
        attributes = {"color": color}
        if layer:
            attributes["layer"] = layer
        msp.add_line(start=start, end=end, dxfattribs=attributes)

    def add_polyline(msp, points, color=1):
        msp.add_lwpolyline(points, close=True, dxfattribs={"color": color})

    def draw_vertical_scale(msp, y_start, y_end):
        add_line(msp, (0, y_start * 10), (0, y_end * 10))
        for qiymet in range(y_start, y_end + 1):
            y_pos = qiymet * 10
            add_line(msp, (-4, y_pos), (0, y_pos))
            add_text(msp, f"{qiymet}m", (-10, y_pos))

    def draw_table_lines(msp, x_current, y_start_table, quyu):
        add_line(msp, (x_current, y_start_table - 18), (x_current, y_start_table - 13), layer="line_layer")
        if quyu[3] == 0:
            add_line(msp, (x_current - 5, y_start_table - 17), (x_current - 5, y_start_table + 4), layer="line_layer")
        else:
            add_text(msp, f"{quyu[3]}", (x_current - ((34 + quyu[3]) / 2), y_start_table - 15))

    def draw_table_headers(msp, y_start_table, x_end):
        headers = [
            ("Quyu No", -3, 0),
            ("Yukseklik, m", -3, -5),
            ("Derinlik, m", -3, -10),
            ("Mesafe, m", -3, -15)
        ]
        for text, x, offset in headers:
            add_text(msp, text, (x, y_start_table + offset))

        horizontal_lines = [3, -3, -8, -13, -18]
        for offset in horizontal_lines:
            add_line(msp, (-5, y_start_table + offset), (x_end + 10, y_start_table + offset), layer="line_layer")

        add_line(msp, (-5, y_start_table + 4), (-5, y_start_table - 17), layer="line_layer")
        add_line(msp, (x_end + 10, y_start_table + 4), (x_end + 10, y_start_table - 17), layer="line_layer")

    def geoloji_kesilis_yarat(quyular):
        doc = ezdxf.new()
        msp = doc.modelspace()

        max_yukseklik = max(quyular.iloc[:, 1])
        min_yukseklik = min(quyular.iloc[:, 1] - quyular.iloc[:, 2])
        y_start = int(min_yukseklik) - 1
        y_end = int(max_yukseklik) + 2
        y_start_table = y_start * 10 - 10

        draw_vertical_scale(msp, y_start, y_end)

        x_pos = 30
        scale_factor = 2
        previous_top = None
        previous_bottom = None
        previous_x = x_pos

        for index, quyu in quyular.iterrows():
            x_current = previous_x + scale_factor * quyu[3]
            y_top = quyu[1] * 10
            y_bottom = (quyu[1] - quyu[2]) * 10
            add_polyline(msp, [(x_current - 2, y_top), (x_current + 2, y_top), (x_current + 2, y_bottom),
                               (x_current - 2, y_bottom)])
            if previous_top:
                add_line(msp, previous_top, (x_current, y_top), color=2)
                add_line(msp, previous_bottom, (x_current, y_bottom), color=2)

            add_text(msp, f"{quyu[0]}", (x_current, y_top + 5))
            add_text(msp, f"{quyu[0]}", (x_current - 2, y_start_table))
            add_text(msp, f"{quyu[1]}", (x_current - 2, y_start_table - 5))
            add_text(msp, f"{quyu[2]}", (x_current - 2, y_start_table - 10))

            draw_table_lines(msp, x_current, y_start_table, quyu)

            previous_top = (x_current, y_top)
            previous_bottom = (x_current, y_bottom)
            previous_x = x_current
            # ------------------------------------------------------------------------------------------------
            layers = laylar[laylar.iloc[:, 0] == quyu[0]].iloc[:, 1].values
            compositions = laylar[laylar.iloc[:, 0] == quyu[0]].iloc[:, 2].values
            height = quyu[1]
            line_length = y_end * 10 + 50
            depth = quyu[2]
            column_widths = [-10, 20, 15, 15, 15, 15, 30, 100, 20, 10, 10]
            if index == 0:
                length_table = 0
            else:
                length_table = index * 270

            draw_vertical_lines(msp, line_length, depth, length_table)
            draw_outer_lines(msp, line_length, depth, length_table)
            draw_columns_and_labels(msp, line_length, depth, column_widths, length_table)
            draw_layer_text(msp, line_length, depth, layers, compositions, length_table, height)
            ident_table(msp, line_length, depth, quyu[0], str(quyu[4]), length_table)

        draw_table_headers(msp, y_start_table, x_current)

        dxf_file_path = os.path.join(settings.MEDIA_ROOT, "geoloji_kesilis_cedvel_setir.dxf")
        doc.saveas(dxf_file_path, encoding="utf-8")
        return dxf_file_path

    def ident_table(msp, line_length, depth, name, place, x_cord_add):
        y_table_start = line_length + depth * 20 + 35
        y_table_end = line_length + depth * 20 + 65

        add_text(msp, name, ((250 - len(name)) / 2 + x_cord_add, y_table_end - 4), 3, bold=True)
        add_text(msp, f"Obyekt: {place}", ((240 - len(place) - 8) / 2 + x_cord_add, y_table_end - 9), 3, font="Tahoma")
        add_text(msp, f"Quyunun dərinliyi: {depth} m", (10 + x_cord_add, y_table_end - 16), 3, bold=True)
        add_text(msp, "Qazma diametri: 132 mm", (10 + x_cord_add, y_table_end - 21), 3, bold=True)
        add_text(msp, f"Quyu ağzının nisbi yüksəkliyi: {depth} m", (130 + x_cord_add, y_table_end - 16), 3, bold=True)
        add_text(msp, "Qazma tarixi: ", (130 + x_cord_add, y_table_end - 21), 3, bold=True)

        borders = [
            ((-10 + x_cord_add, y_table_start), (240 + x_cord_add, y_table_start)),
            ((-10 + x_cord_add, y_table_end), (240 + x_cord_add, y_table_end)),
            ((-10 + x_cord_add, y_table_start), (-10 + x_cord_add, y_table_end)),
            ((240 + x_cord_add, y_table_start), (240 + x_cord_add, y_table_end)),
        ]
        for start, end in borders:
            add_line(msp, start=start, end=end)

    def draw_vertical_lines(msp, line_length, depth, x_cord_add):
        start_point = (0 + x_cord_add, line_length)
        end_point = (0 + x_cord_add, line_length + depth * 20)
        msp.add_line(start_point, end_point)

        y_olcu = line_length + depth * 20
        for idx, olcu in enumerate(range(depth * 20 + 1)):
            y_coord = line_length + olcu

            if olcu % 20 == 0:
                msp.add_line(start=(-4 + x_cord_add, y_coord), end=(0 + x_cord_add, y_coord))
                add_text(msp, idx / 20, (-7 + x_cord_add, y_olcu - 2), bold=True)
                y_olcu -= 20
            elif olcu % 10 == 0:
                msp.add_line(start=(-2 + x_cord_add, y_coord), end=(0 + x_cord_add, y_coord))
            elif olcu % 2 == 0:
                msp.add_line(start=(-1 + x_cord_add, y_coord), end=(0 + x_cord_add, y_coord))

    def draw_outer_lines(msp, line_length, depth, x_cord_add):
        vertical_end = line_length + depth * 20
        borders = [
            ((-10 + x_cord_add, line_length), (240 + x_cord_add, line_length)),
            ((-10 + x_cord_add, vertical_end), (240 + x_cord_add, vertical_end)),
            ((-10 + x_cord_add, vertical_end + 8), (240 + x_cord_add, vertical_end + 8)),
            ((240 + x_cord_add, line_length), (240 + x_cord_add, vertical_end + 30)),
            ((-10 + x_cord_add, vertical_end + 30), (240 + x_cord_add, vertical_end + 30)),
        ]
        for start, end in borders:
            add_line(msp, start=start, end=end)

    def draw_columns_and_labels(msp, line_length, depth, column_widths, x_cord_add):
        col = 0
        headers = ["Dərinilik\nMiqyas\n1:100",
                   "Geoloji\nİndeksi",
                   "Lay dabanının\nmütləq\nhündürlüyü",
                   "   Layın  yatma\n     dərinliyi\n \n \n Dan       Dək", "Qalinliq\n   ,m",
                   "\nSüxurların şərti\n  işarəsi",
                   "\n \n     Süxurların litoloji təsviri",
                   "\nNümunənin\ngötürülmə\ndərinliyi,m",
                   "Qrunt suları\n haqqında\n  məlumat\nRast  Qrunt\ngəlmə  gəlmə ",
                   ]
        vertical_end = line_length + depth * 20
        head_col = 0
        for idx, width in enumerate(column_widths, start=1):

            col += width
            col_text = col - width / 2
            if idx != 2:
                add_text(msp, idx, (col_text - 1 + x_cord_add, vertical_end + 4))
            if (idx == 4) | (idx == 10):
                add_line(msp, start=(col + x_cord_add, line_length), end=(col + x_cord_add, vertical_end + 18))
                add_line(msp, start=(col - width + x_cord_add, vertical_end + 18),
                         end=(col + width + x_cord_add, vertical_end + 18))
            else:
                add_line(msp, start=(col + x_cord_add, line_length), end=(col + x_cord_add, vertical_end + 30))
        add_line(msp, start=(0 + x_cord_add, vertical_end), end=(0 + x_cord_add, vertical_end + 30))
        add_text(msp, 2, (5 + x_cord_add, vertical_end + 4))

        add_vertical_text(msp, headers[0], (column_widths[0] + 1 + x_cord_add, vertical_end + 13), bold=True,
                          font="Tahoma")
        add_vertical_text(msp, headers[1], (1, vertical_end + 13 + x_cord_add), bold=True, font="Tahoma")
        add_vertical_text(msp, headers[2], (sum(column_widths[:2]) + 1 + x_cord_add, vertical_end + 13), bold=True,
                          font="Tahoma", char_height=1.5)
        add_text(msp, headers[3], (sum(column_widths[:3]) + 1 + x_cord_add, vertical_end + 27), bold=True,
                 font="Tahoma")
        add_vertical_text(msp, headers[4], (sum(column_widths[:5]) + 1 + x_cord_add, vertical_end + 13), bold=True,
                          font="Tahoma")
        add_text(msp, headers[5], (sum(column_widths[:6]) + 1 + x_cord_add, vertical_end + 27), bold=True,
                 font="Tahoma")
        add_text(msp, headers[6], (sum(column_widths[:7]) + 1 + x_cord_add, vertical_end + 27), bold=True,
                 font="Tahoma")
        add_text(msp, headers[7], (sum(column_widths[:8]) + 1 + x_cord_add, vertical_end + 27), bold=True,
                 font="Tahoma")
        add_text(msp, headers[8], (sum(column_widths[:9]) + 1 + x_cord_add, vertical_end + 27), bold=True,
                 font="Tahoma")

    def draw_layer_lines(msp, line_length, depth, layers, x_cord_add):
        vertical_end = line_length + depth * 20
        for layer in layers:
            y_coord = vertical_end - layer * 20
            add_line(msp, start=(0 + x_cord_add, y_coord), end=(220 + x_cord_add, y_coord))

    def draw_layer_text(msp, line_length, depth, layers, compositions, x_cord_add, height):
        vertical_end = line_length + depth * 20
        previous_layer = 0
        for layer, composition in zip(layers, compositions):
            y_coord = vertical_end - layer * 20
            y_coord_text = vertical_end - 20 * (layer - (layer - previous_layer) / 2)
            if height >= 0:
                text = round(height - layer, 2)
            else:
                text = round(height + layer, 2)

            add_line(msp, start=(0 + x_cord_add, y_coord), end=(220 + x_cord_add, y_coord))
            add_text(msp, text, (17 + x_cord_add, y_coord + 3), bold=True)
            add_text(msp, previous_layer, (32 + x_cord_add, vertical_end - previous_layer * 20 - 2), bold=True)
            add_text(msp, layer, (47 + x_cord_add, y_coord + 3), bold=True)
            add_text(msp, layer - previous_layer, (62 + x_cord_add, y_coord_text), bold=True)
            add_text(msp, composition, (105 + x_cord_add, y_coord_text), bold=True)
            previous_layer = layer

    def add_vertical_text(msp, text, position, bold=False, font="Tahoma", char_height=2):
        if font not in msp.doc.styles:
            msp.doc.styles.new(font, dxfattribs={"font": font})
        mtext = msp.add_mtext(text, dxfattribs={
            "rotation": 90, "style": font
        })
        mtext.dxf.char_height = char_height
        mtext.set_location(position)

        if bold:
            mtext.dxf.style = "Bold"

    return geoloji_kesilis_yarat(quyular)

