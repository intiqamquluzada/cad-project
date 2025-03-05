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

    def add_text(msp, text, position, height=2, bold=False, font="Times New Roman", color=7):

        doc = msp.doc

        if font not in doc.styles:
            doc.styles.new(font, dxfattribs={"font": font})

        mtext = msp.add_mtext(text, dxfattribs={"char_height": height, "style": font, "style": font, "color": color})
        mtext.set_location(position)

        if bold:
            bold_style = font + "_Bold"
            if bold_style not in doc.styles:
                doc.styles.new(bold_style, dxfattribs={"font": font, "width": 1.2})
            mtext.dxf.style = bold_style

        return mtext

    def add_line(msp, start, end, layer="Default", color=None, bold=False, width=0.12):
        """
        ByLayer və ya xüsusi rənglə xətt çəkən funksiya.
        Əgər 'bold=True' seçilərsə, xətt qalın (Polyline) çəkilir.
        """
        if not layer:
            layer = "Default"

        if layer not in msp.doc.layers:
            msp.doc.layers.add(name=layer)

        attributes = {"layer": layer}

        if color is not None:
            attributes["color"] = color

        if bold:
            # Qalın xətt (Polyline) çək
            msp.add_lwpolyline([start, end], dxfattribs={"const_width": width, **attributes})
        else:
            # Adi xətt çək
            msp.add_line(start=start, end=end, dxfattribs=attributes)

    def add_line_scale(msp, start, end, color=7, layer=None, thickness=0.3):
        attributes = {
            "color": color,
            "lineweight": int(thickness * 100),
        }
        if layer:
            attributes["layer"] = layer

        line = msp.add_line(start=start, end=end, dxfattribs=attributes)
        polyline = msp.add_lwpolyline([start, end], dxfattribs={
            "color": color,
            "lineweight": int(thickness * 100)
        })

        return line, polyline

    def draw_open_polyline(msp, left_top, right_top, left_bottom, right_bottom, color=7):
        add_line(msp, left_bottom, left_top, color=color, bold=True)
        add_line(msp, right_bottom, right_top, color=color, bold=True)
        add_line(msp, left_bottom, right_bottom, color=color, bold=True)

    def draw_vertical_scale(msp, y_start, y_end, previous_x, quyu_miqyas_horizontal, min_value, max_value):
        add_line(msp, (0 + previous_x, y_start * quyu_miqyas_horizontal),
                 (0 + previous_x, y_end * quyu_miqyas_horizontal), bold=True, width=0.3)
        add_line(msp, (-0.6 + previous_x, y_start * quyu_miqyas_horizontal),
                 (-0.6 + previous_x, y_end * quyu_miqyas_horizontal), bold=True, width=0.11)
        y_pos_n = 0
        for i in range(y_end - y_start + 1):

            qiymet = min_value - 1 + i
            y_pos = (y_start + i) * quyu_miqyas_horizontal
            y_pos_2 = (y_start + i - 0.5) * quyu_miqyas_horizontal
            if (y_start + i % 2 == 0) and (i != 0):
                p = (y_start + i - 1) * quyu_miqyas_horizontal
                bold_line_horizontal(msp, (-0.3 + previous_x, y_pos), (-0.3 + previous_x, y_pos_n), 6)
            add_line_scale(msp, (-3 + previous_x, y_pos), (0 + previous_x, y_pos), layer="MyLayer", thickness=0.3)
            if i > 0:
                add_line(msp, (-1.5 + previous_x, y_pos_2), (0 + previous_x, y_pos_2), bold=True, width=0.3)
            add_text(msp, f"{qiymet:.1f}", (-9 + previous_x, y_pos + 1))
            y_pos_n = y_pos
        add_text(msp, "H, m", (-3 + previous_x, y_pos + 5), height=3)

    def draw_table_lines(msp, x_current, y_start_table, quyu, scale_factor_vertical):
        add_line(msp, (x_current, y_start_table - 24), (x_current, y_start_table - 17), layer="MyLayer", bold=True)
        add_line(msp, (x_current, y_start_table - 16), (x_current, y_start_table - 17), layer="MyLayer", bold=True)
        add_line(msp, (x_current, y_start_table - 10), (x_current, y_start_table - 11), layer="MyLayer", bold=True)
        add_line(msp, (x_current, y_start_table - 3), (x_current, y_start_table - 4), layer="MyLayer", bold=True)
        if quyu[4] == 0:
            add_line(msp, (x_current - 8, y_start_table - 24), (x_current - 8, y_start_table + 3), layer="MyLayer",
                     bold=True)
        else:
            add_text(msp, f"{quyu[4]: .1f}", (x_current - ((quyu[4]) * scale_factor_vertical / 2), y_start_table - 19))

    def draw_table_headers(msp, y_start_table, x_end, x_cord_ad):
        headers = [
            (" Quyunun №-si", -8, 0),
            ("Quyuların mütləq\n   yüksəkliyi, m", -9, -5),
            ("  Dərinlik, m", -8, -13),
            (" Quyular arası\n  məsafə, m", -8, -18)
        ]
        for text, x, offset in headers:
            add_text(msp, text, (x + x_cord_ad, y_start_table + offset))

        horizontal_lines = [3, -4, -11, -17, -24]
        for offset in horizontal_lines:
            add_line(msp, (-10 + x_cord_ad, y_start_table + offset), (x_end + 10, y_start_table + offset),
                     layer="MyLayer", bold=True)

        add_line(msp, (-10 + x_cord_ad, y_start_table + 3), (-10 + x_cord_ad, y_start_table - 24), layer="MyLayer",
                 bold=True)
        add_line(msp, (x_end + 10, y_start_table + 3), (x_end + 10, y_start_table - 24), layer="MyLayer", bold=True)

    def geoloji_kesilis_yarat(quyular):
        doc = ezdxf.new("R2007")
        msp = doc.modelspace()
        doc.header["$LWDISPLAY"] = 1
        doc.header["$CELWEIGHT"] = 13

        max_yuksek = max((quyular.iloc[:, 2]) * (1000 / quyular.iloc[:, 6]))
        min_derinlik = min((quyular.iloc[:, 2] - quyular.iloc[:, 3]) * (1000 / quyular.iloc[:, 6]))
        max_yukseklik = max_yuksek - min_derinlik
        min_yukseklik = 0
        y_length = int(max_yukseklik) + 2

        y_start = 0
        x_pos = 20

        previous_x = x_pos

        quyu_kesilis = quyular.iloc[:, 0].unique().tolist()
        quyu_miqyas_horizontal = quyular.iloc[:, 6].unique().tolist()

        for idx, kesilis in enumerate(quyu_kesilis):
            quyu_kes = quyular[quyular.iloc[:, 0] == kesilis]
            quyu_miqyas_horizontal = quyu_kes.iloc[:, 6].unique().tolist()
            previous_top = None
            previous_bottom = None
            quyu_miqyas_horizontal = 1000 / quyu_miqyas_horizontal[0]

            max_yuksek = max((quyu_kes.iloc[:, 2]))
            min_derinlik = min((quyu_kes.iloc[:, 2] - quyu_kes.iloc[:, 3]))
            max_yukseklik = int(max_yuksek) - int(min_derinlik)
            min_yukseklik = 0

            y_start = int(min_yukseklik) - 1
            y_end = int(max_yukseklik) + 2

            y_start_table = y_start * 10 - 10

            if previous_x != x_pos:
                draw_vertical_scale(msp, y_start, y_end, previous_x + 70, quyu_miqyas_horizontal, int(min_derinlik),
                                    int(max_yuksek))
                previous_x += 92
            else:
                draw_vertical_scale(msp, y_start, y_end, 0, quyu_miqyas_horizontal, int(min_derinlik), int(max_yuksek))

            y_top = (y_end - (int(max_yuksek) + 2 - quyu_kes.iloc[0, 2])) * quyu_miqyas_horizontal
            y_bottom = (y_end - (
                        int(max_yuksek) + 2 - (quyu_kes.iloc[0, 2] - quyu_kes.iloc[0, 3]))) * quyu_miqyas_horizontal

            add_line(msp, (previous_x - 11, y_top), (previous_x - 1, y_top), layer="MyLayer", bold=True)
            add_line(msp, (previous_x - 11, y_bottom - 2), (previous_x, y_bottom - 2), layer="MyLayer", bold=True)
            add_line(msp, (previous_x - 11, y_bottom - 2), (previous_x - 11, y_top), layer="MyLayer", bold=True)
            x_cord_add = previous_x

            for index, quyu in quyu_kes.iterrows():
                scale_factor_vertical = 1000 / quyu[5]
                scale_factor_horizontal = 1000 / quyu[6]
                scale_vertical = quyu[5]
                scale_horizontal = quyu[6]

                y_top = (y_end - (int(max_yuksek) + 2 - quyu[2])) * scale_factor_horizontal
                y_bottom = (y_end - (int(max_yuksek) + 2 - (quyu[2] - quyu[3]))) * scale_factor_horizontal
                x_current = previous_x + scale_factor_vertical * quyu[4]

                draw_open_polyline(msp, (x_current - 1, y_top), (x_current + 1, y_top), (x_current - 1, y_bottom),
                                   (x_current + 1, y_bottom))
                if previous_top:
                    add_line(msp, previous_top, (x_current - 1, y_top), color=7, bold=True)
                    add_line(msp, previous_bottom, (x_current, y_bottom - 2), color=7, bold=True)

                add_text(msp, f"{quyu[1]}", (x_current + 1, y_top + 9), height=3)
                add_text(msp, f"{'{:.1f}'.format(quyu[2])}", (x_current + 1, y_top + 5), height=3)
                add_text(msp, f"{'{:.1f}'.format(quyu[3])}", (x_current + 2, y_bottom + 1), height=2)
                add_line(msp, (x_current, y_top), (x_current, y_top + 5.5), color=7, bold=True)
                add_line(msp, (x_current + len(quyu[1]) * 2 + 1, y_top + 5.5), (x_current, y_top + 5.5), color=7,
                         bold=True)
                add_line(msp, (x_current, y_top), (x_current - 0.5, y_top + 3), color=7, bold=True)
                add_line(msp, (x_current + 0.5, y_top + 2), (x_current - 0.5, y_top + 3), color=7, bold=True)

                add_text(msp, f"{quyu[1]}", (x_current - 3, y_start_table))
                add_text(msp, f"{quyu[2]}", (x_current - 3, y_start_table - 7))
                add_text(msp, f"{quyu[3]: .1f}", (x_current - 3, y_start_table - 13))

                # draw_line_with_weight(msp,0,100,y_start_table- 40,70)

                draw_table_lines(msp, x_current, y_start_table, quyu, scale_factor_vertical)

                previous_top = (x_current + 1, y_top)
                previous_bottom = (x_current, y_bottom - 2)

                previous_x = x_current
            if idx == 0:
                x2 = 0
            add_line(msp, (x_current + 1, y_top), (x_current + 10, y_top), layer="MyLayer", bold=True)
            add_line(msp, (x_current, y_bottom - 2), (x_current + 10, y_bottom - 2), layer="MyLayer", bold=True)
            add_line(msp, (x_current + 10, y_bottom - 2), (x_current + 10, y_top), layer="MyLayer", bold=True)
            add_text(msp, f"{kesilis} xətti üzrə geoloji-litoloji kəsiliş",
                     (x_current - (x_current - x2) / 2, y_end * scale_factor_horizontal + 19), height=3, bold=True,
                     font="Times New Roman")
            add_text(msp, f"     Miqyas:  üfüqi: 1:{scale_vertical}",
                     (x_current - (x_current - x2) / 2, y_end * scale_factor_horizontal + 14), height=3, bold=True,
                     font="Times New Roman")
            add_text(msp, f"                   şaquli: 1:{scale_horizontal}",
                     (x_current - (x_current - x2) / 2, y_end * scale_factor_horizontal + 10), height=3, bold=True,
                     font="Times New Roman")
            x2 = x_current
            if idx == 0:
                draw_table_headers(msp, y_start_table, x_current, 0)
                x2 = x_current
            else:
                draw_table_headers(msp, y_start_table, x_current, x_cord_add - 22)

        quyu_layers = laylar.iloc[:, 0].unique().tolist()

        for index, quyu in enumerate(quyu_layers):
            layers = laylar[laylar.iloc[:, 0] == quyu].iloc[:, 1].values
            water = laylar[laylar.iloc[:, 0] == quyu].iloc[:, 3].values
            water_qrunt = laylar[laylar.iloc[:, 0] == quyu].iloc[:, 4].values
            compositions = laylar[laylar.iloc[:, 0] == quyu].iloc[:, 2].values
            height = laylar[laylar.iloc[:, 0] == quyu].iloc[0, 7]
            place = laylar[laylar.iloc[:, 0] == quyu].iloc[0, 6]
            date = laylar[laylar.iloc[:, 0] == quyu].iloc[:, 5].unique()
            line_length = y_length + 50
            depth = laylar[laylar.iloc[:, 0] == quyu].iloc[0, 8]
            # column_widths = [-10, 20, 15, 15, 15, 15, 30, 100, 20, 10, 10]
            column_widths = [-10, 20, 10.5, 10.5, 10.5, 10.5, 24.4, 60.6, 18, 8.5, 8.5]
            if index == 0:
                length_table = 0
            else:
                length_table = index * 200

            if len(date) > 0:
                ident_table(msp, line_length, depth, quyu, place, height, date[0], length_table)
            else:
                ident_table(msp, line_length, depth, quyu, place, height, "", length_table)
            draw_vertical_lines(msp, line_length, depth, length_table)
            draw_outer_lines(msp, line_length, depth, length_table)
            draw_columns_and_labels(msp, line_length, depth, column_widths, length_table)
            draw_layer_text(msp, line_length, depth, layers, compositions, length_table, height)
            if pd.notna(water[0]) and pd.notna(water_qrunt[0]):
                water_line(msp, line_length, depth, water, water_qrunt, length_table)
            elif pd.isna(water[0]) and pd.notna(water_qrunt[0]):
                water_line(msp, line_length, depth, None, water_qrunt, length_table)
            elif pd.notna(water[0]) and pd.isna(water_qrunt[0]):
                water_line(msp, line_length, depth, water, None, length_table)
        # draw_table_headers(msp, y_start_table, x_current)

        dxf_file_path = os.path.join(settings.MEDIA_ROOT, "geoloji_kesilis_cedvel_setir.dxf")
        doc.saveas(dxf_file_path, encoding="utf-8")
        return dxf_file_path

    def ident_table(msp, line_length, depth, name, place, height, date, x_cord_add):
        y_table_start = line_length + depth * 10 + 27
        y_table_end = line_length + depth * 10 + 49

        add_text(msp, name, ((160 - len(name)) / 2 + x_cord_add, y_table_end - 2), 2, bold=True, font="Times New Roman")
        add_text(msp, f"Obyekt: {place}", ((160 - len(place) - 8) / 2 + x_cord_add, y_table_end - 7), 2, bold=True,
                 font="Times New Roman")
        add_text(msp, f"Quyunun dərinliyi: {'{:.1f}'.format(depth)} m", (10 + x_cord_add, y_table_end - 12), 2.3,
                 bold=True, font="Times New Roman")
        add_text(msp, "Qazma diametri: 132 mm", (10 + x_cord_add, y_table_end - 17), 2.3, bold=True)
        add_text(msp, f"Quyu ağzının mütləq yüksəkliyi: {'{:.1f}'.format(height)} m",
                 (95 + x_cord_add, y_table_end - 12), 2.3, bold=True, font="Times New Roman")
        add_text(msp, f"Qazma tarixi: {date} ", (95 + x_cord_add, y_table_end - 17), 2.3, bold=True,
                 font="Times New Roman")

        borders = [
            ((-10 + x_cord_add, y_table_start), (172 + x_cord_add, y_table_start)),
            ((-10 + x_cord_add, y_table_end), (172 + x_cord_add, y_table_end)),
            ((-10 + x_cord_add, y_table_start), (-10 + x_cord_add, y_table_end)),
            ((172 + x_cord_add, y_table_start), (172 + x_cord_add, y_table_end)),
        ]
        for start, end in borders:
            add_line(msp, start=start, end=end, layer="MyLayer", bold=True)

    def water_line(msp, line_length, depth, water, water_qrunt, x_cord_add):
        vertical_end = line_length + depth * 10
        if water is not None:
            for wat in water:
                y_coord = vertical_end - wat * 10
                add_line(msp, start=(155 + x_cord_add, y_coord), end=(163.5 + x_cord_add, y_coord), color=5, bold=True,
                         width=0.3)
                # bold_line_vertical(msp, start=(155+x_cord_add, y_coord), end=(163.5+x_cord_add, y_coord),bold=3,color=5)
                add_text(msp, wat, (157.5 + x_cord_add, y_coord + 3), bold=True, font="Times New Roman", color=5)
        if water_qrunt is not None:
            for wat in water_qrunt:
                y_coord = vertical_end - wat * 10
                add_line(msp, (163.5 + x_cord_add, y_coord), (172 + x_cord_add, y_coord), bold=True, width=0.3, color=5)
                # bold_line_vertical(msp, start=(163.5+x_cord_add, y_coord), end=(172+x_cord_add, y_coord),bold=3,color=5)
                add_text(msp, wat, (166 + x_cord_add, y_coord + 3), bold=True, font="Times New Roman", color=5)

    def draw_vertical_lines(msp, line_length, depth, x_cord_add):
        start_point = (0 + x_cord_add, line_length)
        end_point = (0 + x_cord_add, line_length + depth * 10)
        # bold_line_horizontal(msp,(0+x_cord_add, line_length-2),(0+x_cord_add, line_length + depth * 10),3)
        add_line_scale(msp, start_point, end_point, thickness=0.3)

        y_olcu = line_length + depth * 10
        for idx, olcu in enumerate(range(depth * 10 + 1)):
            y_coord = line_length + olcu

            if olcu % 10 == 0:
                # bold_line_vertical(msp,(-3+x_cord_add, y_coord),(0+x_cord_add, y_coord),3)
                add_line(msp, (-3 + x_cord_add, y_coord), (0 + x_cord_add, y_coord), bold=True, width=0.3)
                if olcu / 10 == 0:
                    add_text(msp, idx / 10, (-8 + x_cord_add, y_olcu), bold=True)
                else:
                    add_text(msp, idx / 10, (-8 + x_cord_add, y_olcu + 1), bold=True)
                y_olcu -= 10
            elif olcu % 5 == 0:
                add_line(msp, (-1.5 + x_cord_add, y_coord), (0 + x_cord_add, y_coord), bold=True, width=0.3)
            elif olcu % 1 == 0:
                add_line(msp, (-0.8 + x_cord_add, y_coord), (0 + x_cord_add, y_coord), bold=True, width=0.3)

    def draw_outer_lines(msp, line_length, depth, x_cord_add):
        vertical_end = line_length + depth * 10
        borders = [
            ((-10 + x_cord_add, line_length - 1), (172 + x_cord_add, line_length - 1)),
            ((0 + x_cord_add, line_length), (172 + x_cord_add, line_length)),
            ((-10 + x_cord_add, vertical_end), (172 + x_cord_add, vertical_end)),
            ((-10 + x_cord_add, vertical_end + 7), (172 + x_cord_add, vertical_end + 7)),
            ((172 + x_cord_add, line_length), (172 + x_cord_add, vertical_end + 23)),
            ((-10 + x_cord_add, vertical_end + 23), (172 + x_cord_add, vertical_end + 23)),
        ]
        for start, end in borders:
            add_line(msp, start=start, end=end, layer="MyLayer", bold=True)

    def draw_columns_and_labels(msp, line_length, depth, column_widths, x_cord_add):
        col = 0
        headers = ["Dərinilik\nMiqyas\n1:100",
                   "Geoloji\nİndeks",
                   "Lay dabanının\n  mütləq\nhündürlüyü,m",
                   "Layın  yatma\n  dərinliyi,m \n \n Dan      Dək", "Qalinliq,\n   m",
                   "\nSüxurların şərti\n      işarəsi",
                   "\n   Süxurların litoloji təsviri",
                   "\nNümunənin\n götürülmə\ndərinliyi,m",
                   " Qrunt suları\n  haqqında\n   məlumat\nRast,   Qərar-\ngəlmə laşma,\n  m          m ",
                   ]
        vertical_end = line_length + depth * 10
        head_col = 0
        for idx, width in enumerate(column_widths, start=1):

            col += width
            col_text = col - width / 2
            if idx != 2:
                add_text(msp, idx, (col_text - 1 + x_cord_add, vertical_end + 4))
            if (idx == 4) | (idx == 10):
                add_line(msp, start=(col + x_cord_add, line_length - 1), end=(col + x_cord_add, vertical_end + 15),
                         layer="MyLayer", bold=True)
                add_line(msp, start=(col - width + x_cord_add, vertical_end + 15),
                         end=(col + width + x_cord_add, vertical_end + 15), layer="MyLayer", bold=True)
            else:
                add_line(msp, start=(col + x_cord_add, line_length - 1), end=(col + x_cord_add, vertical_end + 23),
                         layer="MyLayer", bold=True)
        add_line(msp, start=(0 + x_cord_add, vertical_end), end=(0 + x_cord_add, vertical_end + 23), bold=True)
        add_text(msp, 2, (5 + x_cord_add, vertical_end + 4))

        add_vertical_text(msp, headers[0], (column_widths[0] + 1 + x_cord_add, vertical_end + 9), bold=True,
                          font="Times New Roman")
        add_vertical_text(msp, headers[1], (1 + x_cord_add, vertical_end + 9), bold=True, font="Times New Roman")
        add_vertical_text(msp, headers[2], (sum(column_widths[:2]) + 1 + x_cord_add, vertical_end + 7), bold=True,
                          font="Times New Roman", char_height=1.5)
        add_text(msp, headers[3], (sum(column_widths[:3]) + 1 + x_cord_add, vertical_end + 22), bold=True,
                 font="Times New Roman")
        add_vertical_text(msp, headers[4], (sum(column_widths[:5]) + 1 + x_cord_add, vertical_end + 9), bold=True,
                          font="Times New Roman")
        add_text(msp, headers[5], (sum(column_widths[:6]) + 1 + x_cord_add, vertical_end + 22), bold=True,
                 font="Times New Roman")
        add_text(msp, headers[6], (sum(column_widths[:7]) + 1 + x_cord_add, vertical_end + 22), height=3, bold=True,
                 font="Times New Roman")
        add_text(msp, headers[7], (sum(column_widths[:8]) + 1 + x_cord_add, vertical_end + 22), bold=True,
                 font="Times New Roman")
        add_text(msp, headers[8], (sum(column_widths[:9]) + 1 + x_cord_add, vertical_end + 23), height=1.6, bold=True,
                 font="Times New Roman")

    def draw_layer_text(msp, line_length, depth, layers, compositions, x_cord_add, height):
        vertical_end = line_length + depth * 10
        previous_layer = 0
        for layer, composition in zip(layers, compositions):
            y_coord = vertical_end - layer * 10
            if layer >= 0.30:
                y_coord_text = vertical_end - 10 * (layer - (layer - previous_layer) / 2)
            else:
                y_coord_text = vertical_end
            if height >= 0:
                text = round(height - layer, 2)
            else:
                text = round(height + layer, 2)
            if layer == depth:
                add_text(msp, text, (13 + x_cord_add, y_coord + 2), bold=True)
                add_text(msp, "{:.1f}".format(previous_layer), (24 + x_cord_add, vertical_end - previous_layer * 10),
                         bold=True)
                add_text(msp, "{:.1f}".format(layer), (34 + x_cord_add, y_coord + 2), bold=True)
                add_text(msp, "{:.1f}".format(layer - previous_layer), (44 + x_cord_add, y_coord_text), bold=True)
                add_text(msp, composition, (80 + x_cord_add, y_coord_text), bold=True)
            else:
                add_line(msp, start=(0 + x_cord_add, y_coord), end=(137 + x_cord_add, y_coord), bold=True)
                add_text(msp, text, (13 + x_cord_add, y_coord + 2), bold=True)
                add_text(msp, "{:.1f}".format(previous_layer), (24 + x_cord_add, vertical_end - previous_layer * 10),
                         bold=True)
                add_text(msp, "{:.1f}".format(layer), (24 + x_cord_add, y_coord), bold=True)
                add_text(msp, "{:.1f}".format(layer), (34 + x_cord_add, y_coord + 2), bold=True)
                add_text(msp, "{:.1f}".format(layer - previous_layer), (44 + x_cord_add, y_coord_text), bold=True)
                add_text(msp, composition, (80 + x_cord_add, y_coord_text), bold=True)
            previous_layer = layer
        y_coord_text = vertical_end - 10 * (depth - (depth - layer) / 2)
        # add_text(msp,"{:.1f}".format(depth-previous_layer),(44+x_cord_add,y_coord_text),bold=True)
        # add_text(msp,"{:.1f}".format(depth),(34+x_cord_add,line_length+2),bold=True)
        # add_text(msp,"{:.1f}".format(height-depth),(13+x_cord_add,line_length+2),bold=True)

    def add_vertical_text(msp, text, position, bold=False, font="Times New Roman", char_height=2):

        if font not in msp.doc.styles:
            msp.doc.styles.new(font, dxfattribs={"font": font})
        mtext = msp.add_mtext(text, dxfattribs={
            "rotation": 90, "style": font
        })
        mtext.dxf.char_height = char_height
        mtext.set_location(position)

        if bold:
            mtext.dxf.style = "Bold"

    def bold_line_vertical(msp, start, end, bold, color=7):
        x = -1 * bold / 20
        for i in range(1, bold * 10 + 1):
            add_line(msp, start=(start[0], start[1] + x), end=(end[0], end[1] + x), color=color)
            x += 0.01

    def bold_line_horizontal(msp, start, end, bold):
        x = -1 * bold / 20
        for i in range(1, bold * 10 + 1):
            msp.add_line(start=(start[0] + x, start[1]), end=(end[0] + x, end[1]))
            x += 0.01

    def draw_line_with_weight(msp, x1, x2, y, weight=30):
        """
        0.3 mm (30 ezdxf vahidi) qalınlığında xətt çəkən funksiya.

        :param msp: ModelSpace obyekti
        :param x1: Xəttin başlanğıc nöqtəsinin x koordinatı
        :param x2: Xəttin son nöqtəsinin x koordinatı
        :param y: Xəttin hər iki nöqtəsinin y koordinatı
        :param weight: Xəttin qalınlığı (ezdxf-də 0.01 mm vahidində, 0.3 mm = 30)
        """
        LAYER_NAME = "Thick_Lines"

        # Lay yaradılması (əgər mövcud deyilsə)
        if LAYER_NAME not in msp.doc.layers:
            msp.doc.layers.add(name=LAYER_NAME, lineweight=weight)

        msp.add_line(
            (x1, y),
            (x2, y),
            dxfattribs={
                "layer": LAYER_NAME,
                "lineweight": weight,  # 0.3 mm = 30 (ezdxf-də 0.01 mm vahidində)
            },
        )

    return geoloji_kesilis_yarat(quyular)
