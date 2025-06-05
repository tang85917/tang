import flet as ft


class DashboardApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Flet Dashboard UI"
        self.page.bgcolor = ft.Colors.BLUE_GREY_50
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window.width = 1000
        self.page.window.height = 700
        self.page.padding = 0

        self.page.add(self.build_ui())

    def build_ui(self):
        return ft.Row(
            controls=[
                self.build_sidebar(),
                ft.VerticalDivider(width=1),
                self.build_main_content()
            ],
            expand=True
        )

    def build_sidebar(self):
        return ft.Container(
            width=220,
            bgcolor=ft.Colors.BLUE_GREY_900,
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Text("MyApp", size=24, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    ft.Divider(color=ft.Colors.GREY),
                    self.nav_item("Dashboard", ft.Icons.DASHBOARD),
                    self.nav_item("Profile", ft.Icons.PERSON),
                    self.nav_item("Settings", ft.Icons.SETTINGS),
                    self.nav_item("Logout", ft.Icons.LOGOUT, color=ft.Colors.RED_200),
                    ft.Container(expand=True),
                    ft.Text("v1.0.0", size=12, color=ft.Colors.WHITE54)
                ]
            )
        )

    def nav_item(self, text, icon, color=ft.Colors.WHITE):
        return ft.Container(
            padding=10,
            border_radius=10,
            bgcolor=ft.Colors.BLUE_GREY_800,
            on_click=lambda e: print(f"{text} clicked"),
            content=ft.Row(
                controls=[
                    ft.Icon(icon, color=color, size=20),
                    ft.Text(text, color=color)
                ]
            )
        )

    def build_main_content(self):
        return ft.Container(
            expand=True,
            padding=20,
            content=ft.Column(
                controls=[
                    self.build_appbar(),
                    ft.Container(height=20),
                    self.build_stat_cards(),
                    ft.Container(height=20),
                    self.build_bottom_section()
                ]
            )
        )

    def build_appbar(self):
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("Dashboard", size=28, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        ft.TextField(hint_text="Search...", width=200),
                        ft.IconButton(icon=ft.Icons.NOTIFICATIONS),
                        ft.CircleAvatar(
                            content=ft.Image(src="https://i.pravatar.cc/100", fit="cover"),
                            radius=20
                        )
                    ]
                )
            ]
        )

    def build_stat_cards(self):
        return ft.Row(
            controls=[
                self.stat_card("Users", "1,240", ft.Icons.PERSON, ft.Colors.BLUE_100),
                self.stat_card("Sales", "$12,430", ft.Icons.SHOW_CHART, ft.Colors.GREEN_100),
                self.stat_card("Errors", "8", ft.Icons.ERROR_OUTLINE, ft.Colors.RED_100),
            ],
            spacing=20,
        )

    def stat_card(self, title, value, icon, color):
        return ft.Card(
            content=ft.Container(
                width=230,
                padding=20,
                bgcolor=color,
                border_radius=15,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
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

    def build_bottom_section(self):
        return ft.Row(
            spacing=20,
            controls=[
                self.build_chart_card(),
                self.build_recent_activity()
            ],
            expand=True
        )

    def build_chart_card(self):
        return ft.Card(
            expand=True,
            content=ft.Container(
                padding=20,
                content=ft.Column(
                    controls=[
                        ft.Text("Monthly Revenue", size=18, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            height=150,
                            bgcolor=ft.Colors.BLUE_50,
                            border_radius=10,
                            alignment=ft.alignment.center,
                            content=ft.Text("ここにグラフが入ります", size=14, color=ft.Colors.BLUE_GREY_700),
                        )
                    ]
                )
            )
        )

    def build_recent_activity(self):
        return ft.Card(
            expand=True,
            content=ft.Container(
                padding=20,
                content=ft.Column(
                    controls=[
                        ft.Text("Recent Activity", size=18, weight=ft.FontWeight.BOLD),
                        ft.ListView(
                            expand=True,
                            controls=[
                                self.activity_item("ログイン成功", "1分前"),
                                self.activity_item("ファイルアップロード", "5分前"),
                                self.activity_item("エラー通知", "10分前"),
                                self.activity_item("新規ユーザー登録", "30分前"),
                            ],
                            height=150
                        )
                    ]
                )
            )
        )

    def activity_item(self, description, time):
        return ft.ListTile(
            leading=ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=ft.Colors.GREEN_400),
            title=ft.Text(description),
            subtitle=ft.Text(time, size=12, color=ft.Colors.GREY)
        )


def main(page: ft.Page):
    DashboardApp(page)


ft.app(target=main)
