import flet as ft
from datetime import datetime
import threading
import time
from auth import Sharepoint, Midway
import asyncio
from SP_def import spdef

VERSION = '1.0.1'

sp = spdef()
async def main(page: ft.Page):
    page.title = 'RPMA'
    page.window.width = 1200
    page.window.height = 700
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.with_opacity(0.97, "#F5E6D3")
    page.theme = ft.Theme(color_scheme_seed="#D2B48C")
    
    icon_path = "liu.ico"
    page.window.icon = icon_path
        
    clock_text = ft.Text(
    size=24,
    weight=ft.FontWeight.BOLD,
    )

    date_text = ft.Text(
    size=24,
    weight=ft.FontWeight.BOLD,
    )
    
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            theme_button.icon = ft.Icons.LIGHT_MODE
            theme_button.icon_color = ft.Colors.RED_800
            page.bgcolor = ft.Colors.with_opacity(0.95, ft.Colors.SHADOW)
            page.theme = ft.Theme(color_scheme_seed=ft.Colors.DEEP_PURPLE_900)
            clock_text.color = ft.Colors.RED
            date_text.color = ft.Colors.AMBER_200
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_button.icon = ft.Icons.DARK_MODE
            theme_button.icon_color = ft.Colors.BROWN_800
            page.bgcolor = ft.Colors.with_opacity(0.97, "#F5E6D3")
            page.theme = ft.Theme(color_scheme_seed="#D2B48C")
            clock_text.color = ft.Colors.BROWN_800
            date_text.color = ft.Colors.BROWN_700
        page.update()            
        
    theme_button = ft.IconButton(
        icon=ft.Icons.DARK_MODE,
        icon_color=ft.Colors.BROWN_800,
        tooltip='Switch Mode',
        on_click=toggle_theme
    )
    
    def clock():
        while True:
            try:
                current_time = datetime.now()
                clock_text.value = current_time.strftime('🕒 %H:%M:%S')
                date_text.value = current_time.strftime('📅 %Y/%m/%d')
                page.update()
            except Exception as e:
                print(f'Clock update error: {e}')
            time.sleep(1)
        
    threading.Thread(target=clock, daemon=True).start()
    
    def rp_button(ds: str, bgcolor: str, hover_color:str, on_click):
        button = ft.ElevatedButton(
            text=ds,
            bgcolor=bgcolor,
        )
        
        container = ft.Container(
            content=button,
            animate=ft.Animation(200, ft.AnimationCurve.BOUNCE_OUT),
            scale=1.0,
            animate_rotation=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            rotate=0
        )
        
        def on_hover(e):
            is_hovered = e.data == "true"
            if isinstance(button, ft.ElevatedButton):
                button.bgcolor = hover_color if is_hovered else bgcolor
                button.update()
                container.scale = 1.1 if is_hovered else 1.0
                container.update()

        def on_button_click(e):
            if on_click:
                on_click(e)

            container.rotate = 360
            container.update()
            
            def reset_rotation():
                time.sleep(0.3)
                container.rotate = 0
                container.update()
            
            threading.Thread(target=reset_rotation, daemon=True).start()

        button.on_hover = on_hover
        button.on_click = on_button_click

        return container            
    
    def show_button(filenames: str):
        for filename in filenames:
            ssd_button = filename.startswith('V')
            large_button = filename.startswith('D')
            
        if ssd_button:
            bgcolor = ft.Colors.GREEN_ACCENT_400
            hover_color = ft.Colors.GREEN_900
        elif large_button:
            bgcolor = ft.Colors.INDIGO_300
            hover_color = ft.Colors.INDIGO_900
        else:
            bgcolor = ft.Colors.DEEP_PURPLE_300
            hover_color = ft.Colors.PURPLE_900
            
        button = rp_button(
            ds=filename,
            bgcolor=bgcolor,
            hover_color=hover_color,
            on_click=lambda e: sp.handle_button_click(e, filename)
        )
    
    def search_ds():
        def create_textfield(label: str, view_type: str):
            field = ft.TextField(
                label=label,
                width=200,
                height=40,
                suffix_icon=ft.Icons.OPEN_IN_BROWSER,
                hint_text='Enter Node Code',
                border_color=ft.Colors.BLUE_400,
                focused_border_color=ft.Colors.BLUE_800,
                border_radius=8
            )
            
            async def async_open(e):
                try:
                    sp.open_cortex_roster_sui(None, field.value, view_type)
                    field.border_color = ft.Colors.GREEN_300
                    field.border_width = 3
                except Exception as ex:
                    field.border_color = ft.Colors.RED
                    field.border_width = 3
                finally:
                    field.update()
                    await asyncio.sleep(1.5)
                    field.border_color = ft.Colors.BLUE_400
                    field.border_width = 1
                    field.update()
                        
            def on_submit(e):
                asyncio.create_task(async_open())
                
            field.on_submit = on_submit
            return field
            
        view_types = ['cortex', 'roster', 'sui']
        text_field_map = {}
        
        fields = []
        for view_type in view_types:
            field = create_textfield(label=view_type.capitalize(), view_type=view_type)
            text_field_map[view_type] = field
            fields.append(field)
            
        return ft.Row(fields)
    
    tab_content = ft.Column()
    
    def on_tab_change(e):
        index = tab.selected_index
        tab_content.controls.clear()
        
        if index == 0:
            tab_content.controls.append(ft.Text("🌐 ブラウザ連携表示"))
        elif index == 1:
            tab_content.controls.append(ft.Text("📊 Excelファイル操作"))
        elif index == 2:
            tab_content.controls.append(ft.Text("⬇️ ファイルのダウンロード状況"))
        elif index == 3:
            tab_content.controls.append(ft.Text("ℹ️ DSP 情報表示"))
            
        page.update()
        
    main_title = ft.Container(
        ft.Row([
            ft.Text(
                spans=[
                    ft.TextSpan(
                        'RP Management Application',
                        ft.TextStyle(
                            size=38,
                            weight=ft.FontWeight.BOLD,
                            foreground=ft.Paint(
                                gradient=ft.PaintLinearGradient(
                                    (0, 20), (900, 20), [ft.Colors.RED, ft.Colors.AMBER_500]
                                )
                            )
                        )
                    )
                ]
            )
        ])
    )
    
    tab = ft.Tabs(
        selected_index=0,
        animation_duration=0,
        on_change=on_tab_change,
        tabs=[
            ft.Tab(text='Browser', icon=ft.Icons.LANGUAGE),
            ft.Tab(text="Excel", icon=ft.Icons.TABLE_CHART),
            ft.Tab(text="Download", icon=ft.Icons.DOWNLOAD),
            ft.Tab(text="DSP Info", icon=ft.Icons.INFO),
        ]
    )
    tab_content.controls.append(ft.Text("🌐 ブラウザ連携表示"))
    
    header = ft.Row([
        clock_text, 
        ft.Container(
            content=ft.Row([
                main_title,
                ft.Text(
                    f'Ver. {VERSION}',
                    size=12,
                    color=ft.Colors.BLUE_400,
                )
            ])
        ),
        ft.Container(
            content=ft.Row([
                date_text, theme_button
            ])
        )
    ],
    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )
    
    search_area = ft.Row([
        tab,
        search_ds()
    ], spacing=50)

    page.add(header, search_area, tab, tab_content)

ft.app(target=main)