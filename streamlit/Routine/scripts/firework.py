import sys
import random
import math
from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QRadialGradient

class Firework:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.particles = []
        self.sparks = []
        self.age = 0
        self.exploded = False
        self.size = random.randint(50, 100)
        self.life_time = 0
        
        self.colors = [
            QColor(255, 50, 50),    # 赤
            QColor(50, 255, 50),    # 緑
            QColor(50, 50, 255),    # 青
            QColor(255, 255, 50),   # 黄
            QColor(255, 50, 255),   # マゼンタ
            QColor(50, 255, 255),   # シアン
            QColor(255, 255, 255),  # 白
        ]
        self.color = random.choice(self.colors)
        
    def explode(self):
        self.exploded = True
        num_particles = random.randint(50, 80)
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 8)
            self.particles.append({
                'x': self.x,
                'y': self.y,
                'dx': speed * math.cos(angle),
                'dy': speed * math.sin(angle),
                'size': random.uniform(2, 4),
                'alpha': 255.0,
                'trail': []
            })
        
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            self.sparks.append({
                'x': self.x,
                'y': self.y,
                'dx': speed * math.cos(angle),
                'dy': speed * math.sin(angle),
                'life': 255.0
            })

class FireworkDisplay(QLabel):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                          Qt.WindowType.WindowStaysOnTopHint | 
                          Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setFixedSize(1000, 800)
        self.fireworks = []
        self.project_time = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)
        
        self.launch_timer = QTimer()
        self.launch_timer.timeout.connect(self.launch_firework)
        self.launch_timer.start(1500)

    def launch_firework(self):  
        if len(self.fireworks) < 3:
            x = random.randint(100, self.width() - 100)
            self.fireworks.append(Firework(x, self.height()))
    def update_animation(self):
        # プロジェクト時間を更新
        self.project_time += 16  # 16ミリ秒ごとに増加
        
        # 5秒（5000ミリ秒）経過したらアプリケーションを終了
        if self.project_time >= 10000:
            QApplication.quit()
            return

        # 以下は前と同じ
        for firework in self.fireworks[:]:
            if not firework.exploded:
                firework.y -= 15
                if firework.y < random.randint(100, 400):
                    firework.explode()
            else:
                firework.life_time += 16
                fade_speed = 255 / (3000 / 16)

                for particle in firework.particles[:]:
                    particle['trail'].append((particle['x'], particle['y']))
                    if len(particle['trail']) > 10:
                        particle['trail'].pop(0)
                    
                    particle['x'] += particle['dx']
                    particle['y'] += particle['dy']
                    particle['dy'] += 0.15
                    particle['alpha'] -= fade_speed
                    if particle['alpha'] <= 0:
                        firework.particles.remove(particle)
                
                for spark in firework.sparks[:]:
                    spark['x'] += spark['dx']
                    spark['y'] += spark['dy']
                    spark['dy'] += 0.2
                    spark['life'] -= fade_speed
                    if spark['life'] <= 0:
                        firework.sparks.remove(spark)
                
                if firework.life_time >= 3000 or (not firework.particles and not firework.sparks):
                    self.fireworks.remove(firework)
        
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for firework in self.fireworks:
            if not firework.exploded:
                gradient = QRadialGradient(firework.x, firework.y, 10)
                gradient.setColorAt(0, QColor(255, 255, 200, 150))
                gradient.setColorAt(1, QColor(255, 255, 200, 0))
                painter.setBrush(gradient)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(int(firework.x - 10), int(firework.y - 10), 20, 20)
            else:
                for particle in firework.particles:
                    # グロー効果
                    glow_color = QColor(firework.color)
                    glow_color.setAlpha(int(particle['alpha'] * 0.3))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(glow_color)
                    size = particle['size'] * 2
                    painter.drawEllipse(
                        int(particle['x'] - size),
                        int(particle['y'] - size),
                        int(size * 2),
                        int(size * 2)
                    )
                    
                    # メインのパーティクル
                    color = QColor(firework.color)
                    color.setAlpha(int(particle['alpha']))
                    painter.setBrush(color)
                    painter.drawEllipse(
                        int(particle['x'] - particle['size']),
                        int(particle['y'] - particle['size']),
                        int(particle['size'] * 2),
                        int(particle['size'] * 2)
                    )
                    
                    # 軌跡
                    if len(particle['trail']) > 1:
                        for i in range(len(particle['trail']) - 1):
                            trail_alpha = int(particle['alpha'] * (i / len(particle['trail'])))
                            if trail_alpha > 0:
                                painter.setPen(QColor(firework.color.red(), 
                                                    firework.color.green(), 
                                                    firework.color.blue(), 
                                                    trail_alpha))
                                painter.drawLine(
                                    int(particle['trail'][i][0]),
                                    int(particle['trail'][i][1]),
                                    int(particle['trail'][i+1][0]),
                                    int(particle['trail'][i+1][1])
                                )
                
                # 火花エフェクト
                for spark in firework.sparks:
                    spark_color = QColor(255, 255, 200, int(spark['life']))
                    painter.setBrush(spark_color)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(
                        int(spark['x'] - 1),
                        int(spark['y'] - 1),
                        2, 2
                    )

    def mousePressEvent(self, event):
        if len(self.fireworks) < 3:
            self.fireworks.append(Firework(event.pos().x(), self.height()))

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.pos() - self.pos())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    display = FireworkDisplay()
    display.show()
    sys.exit(app.exec())
