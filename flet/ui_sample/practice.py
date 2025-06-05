import flet as ft
from flet import Colors, Container, Row, Column, Icons

class DashboardApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = 'Flet DashboardApp'
        self.page.bgcolor = Colors.BLUE_GREY_50
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.width = 1000
        self.page.window.height = 700
        self.page.padding = 0
        
        self.page.add(self.build_ui())
        
    def build_ui(self):
        return Row(
            controls=[
                self.build_sidebar(),
                ft.VerticalDivider(width=1),
                self.build_main_content()
            ],
            expand=True
        )
        
    def build_sidebar(self):
        return Container(
            width=220,
            bgcolor=Colors.BLUE_GREY_900,
            padding=20,
            content=Column(
                controls=[
                    ft.Text('MyApp', size=24, color=Colors.AMBER,weight=ft.FontWeight.BOLD),
                    ft.Divider(color=Colors.GREY),
                    self.nav_item("Dashboard", Icons.DASHBOARD),
                    self.nav_item("Profile", Icons.PERSON),
                    self.nav_item("Settings", Icons.SETTINGS),
                    self.nav_item("Logout", Icons.LOGOUT, color=Colors.RED_200),
                    Container(expand=True),
                    ft.Text("v1.0.0", size=12, color=Colors.WHITE54)
                ]
            )
        )
        
    def nav_item(self, text, icon, color=Colors.WHITE):
        return Container(
            padding=10,
            border_radius=10,
            bgcolor=Colors.BLUE_GREY_800,
            on_click=lambda e: print(f'{text} clicked'),
            content=Row(
                controls=[
                    ft.Icon(icon, color=color, size=20),
                    ft.Text(text, color=color)
                ]
            )
        )
        
    def build_main_content(self):
        return Container(
            expand=True,
            padding=20,
            content=Column(
                controls=[
                    self.build_appbar(),
                    Container(height=20),
                    self.build_stat_cards(),
                    Container(height=20),
                    self.build_bottom_secton()
                ]
            )
        )
        
    def build_appbar(self):
        return Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text('Dashboard', size=28, weight=ft.FontWeight.BOLD),
                Row(
                    controls=[
                        ft.TextField(hint_text='Search...', width=200),
                        ft.IconButton(icon=Icons.NOTIFICATIONS),
                        ft.CircleAvatar(
                            content=ft.Image(src='https://i.pravatar.cc/100', fit='cover'),
                            radius=20
                        )
                    ]
                )
            ]
        )
        
    def build_stat_cards(self):
        return Row(
            controls=[
                self.stat_card('Users', '1,240', Icons.PERSON, Colors.BLUE_100),
                self.stat_card('Sales', '$12,430', Icons.SHOW_CHART, Colors.GREEN_100),
                self.stat_card('Errors', '8', Icons.ERROR_OUTLINE, Colors.RED_100)
            ],
            spacing=20
        )
        
    def stat_card(self, title, value, icon, color):
        return ft.Card(
            content=Container(
                width=230,
                padding=20,
                bgcolor=color,
                border_radius=15,
                content=Column(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(title, size=16),
                                ft.Icon(icon, size=20)
                            ]
                        ),
                        ft.Text(value, size=26, weight=ft.FontWeight.BOLD)
                    ]
                )
            )
        )
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
def main(page: ft.Page):
    DashboardApp(page)
    
ft.app(target=main)  