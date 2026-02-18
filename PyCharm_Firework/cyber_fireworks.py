"""
基于pygame的烟花模拟程序
直接运行本程序可以实现通过空格放烟花的效果
"""

import pygame
import random
import math
import sys

# ==================== 初始化设置 ====================
pygame.init()
pygame.mixer.init()

# 初始窗口尺寸
INITIAL_WIDTH, INITIAL_HEIGHT = 1200, 800
screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("赛博烟花")

# 全局变量 - 导出供其他模块使用
WIDTH = INITIAL_WIDTH
HEIGHT = INITIAL_HEIGHT

# ==================== 颜色定义 ====================
BLACK = (0, 0, 0)
BLACK_ALPHA = (0, 0, 0, 25)
CYBER_COLORS = [
    (0, 255, 255),    # 青色
    (255, 0, 255),    # 洋红
    (0, 255, 0),      # 亮绿
    (255, 255, 0),    # 黄色
    (0, 0, 255),      # 蓝色
    (255, 0, 0),      # 红色
    (255, 128, 0),    # 橙色
    (128, 0, 255),    # 紫色
]

# ==================== 音效管理类 ====================
class SoundManager:
    """音效管理类"""
    def __init__(self):
        self.launch_sound = None
        self.explosion_sound = None
        self.create_launch_sound()
        self.create_explosion_sound()

    def create_launch_sound(self):
        """创建上升音效"""
        try:
            duration = 0.8
            sample_rate = 44100
            samples = int(sample_rate * duration)

            sound_data = bytearray()
            for i in range(samples):
                t = i / sample_rate
                freq = 4000 - 1000 * t

                if t < 0.5:
                    amplitude = int(32767 * 0.25)
                else:
                    amplitude = int(32767 * 0.25 * math.exp(-(t - 0.5) * 10))

                value = int(amplitude * (
                    0.6 * math.sin(2 * math.pi * freq * t) +
                    0.3 * math.sin(2 * math.pi * freq * 2 * t) +
                    0.1 * math.sin(2 * math.pi * freq * 3 * t)
                ))

                sound_data.append(value & 0xFF)
                sound_data.append((value >> 8) & 0xFF)
                sound_data.append(value & 0xFF)
                sound_data.append((value >> 8) & 0xFF)

            self.launch_sound = pygame.mixer.Sound(buffer=bytes(sound_data))
            print("上升音效创建成功")
        except Exception as e:
            print(f"上升音效创建失败: {e}")

    def create_explosion_sound(self):
        """创建爆炸音效"""
        try:
            duration = 1.0
            sample_rate = 44100
            samples = int(sample_rate * duration)

            sound_data = bytearray()
            for i in range(samples):
                t = i / sample_rate

                if t < 0.4:
                    freq = 80
                    amplitude = int(32767 * 0.7 * math.exp(-t * 6))
                    main_sound = int(amplitude * math.sin(2 * math.pi * freq * t))
                    noise_amp = amplitude // 2
                    noise = random.randint(-noise_amp, noise_amp)
                else:
                    echo1_delay = 0.15
                    echo2_delay = 0.3
                    echo3_delay = 0.45
                    echo4_delay = 0.6

                    amp1 = int(32767 * 0.4 * math.exp(-(t - echo1_delay) * 4)) if t > echo1_delay else 0
                    amp2 = int(32767 * 0.25 * math.exp(-(t - echo2_delay) * 4)) if t > echo2_delay else 0
                    amp3 = int(32767 * 0.15 * math.exp(-(t - echo3_delay) * 4)) if t > echo3_delay else 0
                    amp4 = int(32767 * 0.08 * math.exp(-(t - echo4_delay) * 4)) if t > echo4_delay else 0

                    echo1 = int(amp1 * math.sin(2 * math.pi * 70 * (t - echo1_delay))) if t > echo1_delay else 0
                    echo2 = int(amp2 * math.sin(2 * math.pi * 65 * (t - echo2_delay))) if t > echo2_delay else 0
                    echo3 = int(amp3 * math.sin(2 * math.pi * 60 * (t - echo3_delay))) if t > echo3_delay else 0
                    echo4 = int(amp4 * math.sin(2 * math.pi * 55 * (t - echo4_delay))) if t > echo4_delay else 0

                    main_sound = echo1 + echo2 + echo3 + echo4
                    noise = random.randint(-2000, 2000)

                value = main_sound + noise
                value = max(-32767, min(32767, value))

                sound_data.append(value & 0xFF)
                sound_data.append((value >> 8) & 0xFF)
                sound_data.append(value & 0xFF)
                sound_data.append((value >> 8) & 0xFF)

            self.explosion_sound = pygame.mixer.Sound(buffer=bytes(sound_data))
            print("爆炸音效创建成功")
        except Exception as e:
            print(f"爆炸音效创建失败: {e}")

    def play_launch(self):
        """播放上升音效"""
        if self.launch_sound:
            try:
                self.launch_sound.play()
            except:
                pass

    def play_explosion(self):
        """播放爆炸音效"""
        if self.explosion_sound:
            try:
                self.explosion_sound.play()
            except:
                pass


# ==================== 粒子类 ====================
class Particle:
    """烟花爆炸后的粒子类"""
    def __init__(self, x, y, color, vx, vy, size=3):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx
        self.vy = vy
        self.size = size
        self.life = 100
        self.gravity = 0.1
        self.fade = random.uniform(0.92, 0.98)
        self.trail = []

    def update(self):
        """更新粒子状态"""
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.life *= self.fade
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)

    def draw(self, surface):
        """绘制粒子"""
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(150 * (i / len(self.trail)) * (self.life / 100))
            if alpha > 10:
                size = max(1, int(self.size * 0.5))
                color = tuple(c * alpha // 255 for c in self.color)
                pygame.draw.circle(surface, color, (int(tx), int(ty)), size)

        if self.life > 10:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
            highlight = tuple(min(255, c + 100) for c in self.color)
            pygame.draw.circle(surface, highlight, (int(self.x), int(self.y)), max(1, self.size//2))

    def is_dead(self):
        """检查粒子是否消亡"""
        return self.life < 5 or self.y > HEIGHT + 50


# ==================== 烟花类 ====================
class Firework:
    """烟花类"""
    def __init__(self, sound_manager=None):
        self.x = random.randint(100, WIDTH - 100)
        self.y = HEIGHT + 20
        self.color = random.choice(CYBER_COLORS)
        self.vy = random.uniform(-14, -10)
        self.particles = []
        self.exploded = False
        self.target_y = random.randint(100, HEIGHT // 2)
        self.size = random.randint(3, 5)
        self.sound_manager = sound_manager
        self.has_played_launch = False
        self.has_played_explosion = False

    def update(self):
        """更新烟花状态"""
        if not self.exploded:
            self.y += self.vy
            self.vy += 0.15

            if not self.has_played_launch and self.sound_manager:
                self.sound_manager.play_launch()
                self.has_played_launch = True

            if self.vy >= -1 or self.y <= self.target_y:
                self.explode()
        else:
            for p in self.particles[:]:
                p.update()
                if p.is_dead():
                    self.particles.remove(p)

    def explode(self):
        """烟花爆炸"""
        if self.exploded:
            return

        self.exploded = True

        if self.sound_manager and not self.has_played_explosion:
            self.sound_manager.play_explosion()
            self.has_played_explosion = True

        num = random.randint(120, 180)
        for i in range(num):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 7)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            color = tuple(max(0, min(255, c + random.randint(-30, 30))) for c in self.color)
            p = Particle(self.x, self.y, color, vx, vy, random.randint(2, 4))
            self.particles.append(p)

    def draw(self, surface):
        """绘制烟花"""
        if not self.exploded:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
            for i in range(2):
                y = self.y + (i+1) * 8
                if y < HEIGHT:
                    alpha = 150 - i * 50
                    color = tuple(c * alpha // 255 for c in self.color)
                    pygame.draw.circle(surface, color, (int(self.x), int(y)), max(1, self.size-1))
        else:
            for p in self.particles:
                p.draw(surface)

    def is_dead(self):
        """检查烟花是否消亡"""
        return self.exploded and len(self.particles) == 0


# ==================== 烟花管理器类 ====================
class FireworkManager:
    """烟花管理器"""
    def __init__(self):
        self.fireworks = []
        self.sound_manager = SoundManager()

    def create_firework(self):
        """创建一个新烟花"""
        fw = Firework(self.sound_manager)
        fw.y = HEIGHT - random.randint(20, 50)
        return fw

    def add_firework(self):
        """添加一个烟花"""
        self.fireworks.append(self.create_firework())
        print(f"添加新烟花，当前数量: {len(self.fireworks)}")

    def update(self):
        """更新所有烟花"""
        for fw in self.fireworks[:]:
            fw.update()
            if fw.is_dead():
                self.fireworks.remove(fw)

    def draw(self, surface):
        """绘制所有烟花"""
        for fw in self.fireworks:
            fw.draw(surface)

    def clear(self):
        """清除所有烟花"""
        self.fireworks.clear()

    def get_firework_count(self):
        """获取当前烟花数量"""
        return len(self.fireworks)


# ==================== 启动界面类 ====================
class StartScreen:
    """启动界面类"""
    def __init__(self):
        self.phase = 0
        self.particles = []
        self.button_hover = False
        self.flash = 0

        for _ in range(40):
            self.particles.append({
                'x': random.randint(0, WIDTH),
                'y': random.randint(0, HEIGHT),
                'size': random.randint(1, 2),
                'speed': random.uniform(0.3, 1),
                'color': random.choice(CYBER_COLORS)
            })

        font_path = 'C:/Windows/Fonts/simhei.ttf'
        try:
            self.font_large = pygame.font.Font(font_path, 100)
            self.font_medium = pygame.font.Font(font_path, 40)
            self.font_small = pygame.font.Font(font_path, 28)
        except:
            self.font_large = pygame.font.Font(None, 100)
            self.font_medium = pygame.font.Font(None, 40)
            self.font_small = pygame.font.Font(None, 28)

    def update(self):
        """更新界面"""
        self.phase += 0.03
        self.flash = (self.flash + 1) % 60

        for p in self.particles:
            p['y'] += p['speed']
            if p['y'] > HEIGHT:
                p['y'] = 0
                p['x'] = random.randint(0, WIDTH)

    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            btn = pygame.Rect(WIDTH//2 - 80, HEIGHT//2 + 150, 160, 50)
            self.button_hover = btn.collidepoint(mx, my)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.button_hover:
            return True
        return False

    def draw(self, surface):
        """绘制界面"""
        surface.fill((5, 5, 15))

        for x in range(0, WIDTH, 60):
            pygame.draw.line(surface, (20, 30, 50), (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 60):
            pygame.draw.line(surface, (20, 30, 50), (0, y), (WIDTH, y), 1)

        for p in self.particles:
            pygame.draw.circle(surface, p['color'], (int(p['x']), int(p['y'])), p['size'])

        title = self.font_large.render("赛博天空", True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))
        surface.blit(title, title_rect)

        rules = ["空格键 - 发射烟花", "ESC - 返回菜单", "拖动边缘 - 调整窗口"]
        y = HEIGHT//2
        for rule in rules:
            text = self.font_small.render(rule, True, (150, 180, 255))
            rect = text.get_rect(center=(WIDTH//2, y))
            surface.blit(text, rect)
            y += 35

        btn_rect = pygame.Rect(WIDTH//2 - 80, HEIGHT//2 + 150, 160, 50)
        btn_color = (80, 120, 255) if self.button_hover else (0, 60, 180)

        pygame.draw.rect(surface, btn_color, btn_rect, border_radius=5)
        pygame.draw.rect(surface, (100, 200, 255), btn_rect, 2, border_radius=5)

        btn_text = self.font_medium.render("进 入", True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=btn_rect.center)
        surface.blit(btn_text, btn_text_rect)


# ==================== 主函数 ====================
def main():
    """主函数"""
    global WIDTH, HEIGHT, screen

    clock = pygame.time.Clock()
    running = True
    in_game = False

    print("\n" + "="*50)
    print("赛博烟花程序启动")
    print("="*50)

    firework_manager = FireworkManager()
    start_screen = StartScreen()
    fade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    fade.fill(BLACK_ALPHA)

    print("\n程序初始化完成")

    # ==================== 游戏主循环 ====================
    while running:
        # ----- 1. 事件处理模块 -----
        # 处理所有用户输入和系统事件
        for event in pygame.event.get():  # 获取所有待处理的事件
            # 处理窗口关闭事件（点击右上角X）
            if event.type == pygame.QUIT:
                running = False  # 设置运行标志为False，退出循环

            # 处理窗口大小改变事件（用户拖动窗口边缘）
            elif event.type == pygame.VIDEORESIZE:
                # 更新全局窗口尺寸变量
                WIDTH, HEIGHT = event.w, event.h
                # 重新创建窗口，保持可调整大小属性
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                # 重新创建拖尾效果的透明表面
                fade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                fade.fill(BLACK_ALPHA)  # 填充半透明黑色

            # 处理键盘按键事件
            elif event.type == pygame.KEYDOWN:
                # ESC键处理
                if event.key == pygame.K_ESCAPE:
                    if in_game:
                        # 如果在游戏中，按ESC返回主菜单
                        in_game = False
                        firework_manager.clear()  # 清除所有烟花
                    else:
                        # 如果在菜单界面，按ESC退出程序
                        running = False
                # 空格键处理（只在游戏中有效）
                elif event.key == pygame.K_SPACE and in_game:
                    # 添加一个新烟花（由本地空格键触发）
                    firework_manager.add_firework()

            # 处理开始界面的事件（只在非游戏状态）
            if not in_game:
                # 将事件传递给开始界面处理（如按钮点击）
                if start_screen.handle_event(event):
                    # 如果开始界面返回True（点击了进入按钮），进入游戏
                    in_game = True

        # ----- 2. 游戏逻辑更新模块 -----
        if in_game:
            # 更新所有烟花的状态（位置、爆炸、粒子效果等）
            firework_manager.update()

            # ----- 3. 画面绘制模块 -----
            # 清空屏幕为黑色
            screen.fill(BLACK)

            # 绘制拖尾效果：在现有画面上覆盖一层半透明黑色
            # 这样之前的画面会逐渐变暗，产生烟花拖尾效果
            screen.blit(fade, (0, 0))

            # 绘制所有烟花（包括未爆炸的烟花和爆炸后的粒子）
            firework_manager.draw(screen)

            # 如果没有烟花在屏幕上，显示提示信息
            if firework_manager.get_firework_count() == 0:
                # 创建提示文本
                tip = start_screen.font_small.render("按空格键发射烟花", True, (100, 150, 255))
                # 获取文本矩形并居中定位
                tip_rect = tip.get_rect(center=(WIDTH // 2, HEIGHT - 50))

                # 创建文本背景（半透明黑色框）
                bg = pygame.Surface((tip_rect.width + 20, tip_rect.height + 10))
                bg.fill((0, 0, 0))  # 填充黑色
                bg.set_alpha(100)  # 设置透明度为100/255
                # 绘制背景
                screen.blit(bg, (tip_rect.x - 10, tip_rect.y - 5))
                # 绘制文本
                screen.blit(tip, tip_rect)

        else:
            # ----- 菜单界面处理 -----
            # 更新开始界面的动画效果
            start_screen.update()
            # 绘制开始界面
            start_screen.draw(screen)

        # ----- 4. 显示更新模块 -----
        # 将所有绘制的内容显示到屏幕上
        pygame.display.flip()

        # 控制游戏帧率为60帧/秒
        # 这样可以限制CPU使用率，并保持动画流畅
        clock.tick(60)

    # ==================== 程序退出清理 ====================
    # 退出pygame（释放资源）
    pygame.quit()
    # 退出程序
    sys.exit()


if __name__ == "__main__":
    main()