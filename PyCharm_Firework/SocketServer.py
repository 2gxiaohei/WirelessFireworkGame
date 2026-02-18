"""
一个简单的Socket服务器实现
负责接收客户端消息，触发烟花发射
出于实现的功能比较简单，程序将烟花显示和Socket服务器整合在一起
当收到客户端的"fire"命令时，直接调用烟花管理器发射烟花，同时支持电脑空格键发射烟花的功能
"""

# ==================== 导入模块 ====================
import socket      # 提供网络通信功能，用于创建TCP服务器
import threading   # 提供多线程支持，可以同时处理多个客户端连接
import pygame      # 游戏开发库，用于显示烟花效果
import sys         # 系统相关功能，用于退出程序

# 从烟花模块导入需要的类和变量
from cyber_fireworks import FireworkManager  # 烟花管理器，负责烟花的创建和更新
from cyber_fireworks import StartScreen      # 开始界面类
from cyber_fireworks import WIDTH as FW_WIDTH   # 窗口宽度（从烟花模块导入）
from cyber_fireworks import HEIGHT as FW_HEIGHT # 窗口高度（从烟花模块导入）
from cyber_fireworks import BLACK, BLACK_ALPHA  # 颜色常量

# ==================== 全局变量 ====================
# 从烟花模块获取窗口尺寸
WIDTH = FW_WIDTH
HEIGHT = FW_HEIGHT
# 创建屏幕对象（后面会在main函数中初始化）
screen = None
# ==================== Socket服务器类 ====================
class SimpleSocketServer:
    def __init__(self, host='你的主机IP', port=8888):
        """
        初始化服务器
        参数:
            host: 服务器默认IP地址，请修改为当前电脑的IP
            port: 服务器默认端口号，客户端需要连接这个端口
        """
        self.host = host          # 保存主机地址
        self.port = port          # 保存端口号
        self.server_socket = None # 服务器socket对象，后面创建
        self.running = False      # 服务器运行状态标志
        self.firework_manager = None  # 烟花管理器引用，用于控制烟花

    def start(self, firework_manager):
        """
        启动服务器
        参数:
            firework_manager: 烟花管理器实例，用于控制烟花发射
        """
        # 保存烟花管理器引用
        self.firework_manager = firework_manager
        self.running = True

        try:
            # ----- 创建TCP socket -----
            # socket.AF_INET: 使用IPv4地址
            # socket.SOCK_STREAM: 使用TCP协议
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # ----- 设置socket选项 -----
            # SO_REUSEADDR: 允许地址重用，这样服务器关闭后可以立即重启（value为1开启这个选项）
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # ----- 绑定地址和端口 -----
            # 将socket绑定到指定的IP和端口
            self.server_socket.bind((self.host, self.port))

            # ----- 开始监听 -----
            # 最大等待连接数为5，超过的客户端会被拒绝
            self.server_socket.listen(5)

            print(f"服务器启动成功，监听端口: {self.port}")

            # ----- 启动接受连接的线程 -----
            # 创建一个后台线程来接受客户端连接
            # 使用线程是因为accept()函数会阻塞，如果不使用线程，游戏界面会卡住
            thread = threading.Thread(target=self._accept_clients)
            thread.daemon = True  # 设置为守护线程，主程序退出时自动结束
            thread.start()

        except Exception as e:
            print(f"服务器启动失败: {e}")

    def _accept_clients(self):
        """
        接受客户端连接的线程函数
        本函数在后台一直运行，等待新的客户端连接
        每接受一个连接，就创建一个新的处理线程
        """
        while self.running:#只要服务器还在运行，就一直执行
            try:
                # ----- 接受新连接 -----
                # accept()会阻塞，直到有客户端连接
                # 返回新的socket对象和客户端地址
                client_socket, address = self.server_socket.accept()
                print(f"客户端连接: {address}")

                # ----- 创建客户端处理线程 -----
                # 为每个连接的客户端创建一个处理线程
                # 这样多个客户端可以同时发送消息，互不影响
                client_thread = threading.Thread(
                    target=self._handle_client,#指定在新线程中运行的函数
                    args=(client_socket, address)#传递给函数的参数（客户端的socket和地址组成的元组）
                )
                client_thread.daemon = True
                client_thread.start()

            except Exception as e:
                if self.running:
                    print(f"接受连接错误: {e}")

    def _handle_client(self, client_socket, address):
        """
        处理单个客户端消息的线程函数
        参数:
            client_socket: 客户端的socket对象
            address: 客户端地址(IP, port)
        """
        try:
            # ----- 循环接收客户端消息 -----
            while self.running:
                # 接收最多1024字节的数据
                # 如果客户端断开连接，recv会返回空数据
                # 如果客户端连接但没有数据，这一行会卡住（阻塞），不会继续执行
                data = client_socket.recv(1024)
                if not data:
                    break  # 客户端断开连接

                # ----- 解析消息 -----
                # 将接收到的字节数据解码为字符串，并去除首尾空白
                message = data.decode('utf-8').strip()
                print(f"收到消息 [{address}]: {message}")

                # ----- 处理消息并生成响应 -----
                response = self._process_message(message)#调用处理消息函数

                # ----- 发送响应 -----
                # 将响应编码为字节并发送回客户端
                client_socket.send(response.encode('utf-8'))

        except Exception as e:
            print(f"客户端处理错误: {e}")
        finally:
            # ----- 清理资源 -----
            # 无论是否出错，都要关闭客户端连接
            client_socket.close()
            print(f"客户端断开: {address}")

    def _process_message(self, message):
        """
        处理消息内容
        参数:
            message: 接收到的消息字符串
        返回:
            要发送回客户端的响应字符串
        """
        # 将消息转为小写，方便比较（不区分大小写）
        message = message.lower()

        # ----- 处理"fire"命令（放一个烟花的命令） -----
        if message == "fire":
            # 检查烟花管理器是否存在
            if self.firework_manager:
                # 调用烟花管理器的add_firework()方法添加一个烟花
                self.firework_manager.add_firework()
                # 获取当前烟花数量
                count = self.firework_manager.get_firework_count()
                return f"烟花发射成功，当前数量: {count}"
            else:
                return "烟花管理器未初始化"
        else:
            # ----- 预留拓展：用于处理其他消息 -----
            # 对于其他消息，目前简单地回复"收到: 消息内容"
            return f"收到: {message}"

    def stop(self):
        """
        停止服务器，关闭所有连接并释放资源
        """
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("服务器已关闭")


# ==================== 主函数 ====================
def main():
    """
    主函数
    程序同时运行两个部分：
    - 前台：pygame游戏界面，显示烟花效果
    - 后台：Socket服务器，接收网络命令
    """
    # 声明要修改的全局变量
    global WIDTH, HEIGHT, screen

    # ========== 1. 初始化pygame ==========
    # pygame是一个游戏开发库，这里用来显示烟花效果
    pygame.init()

    # ========== 2. 创建游戏窗口 ==========
    # pygame.RESIZABLE 表示窗口可以调整大小
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    # 设置窗口标题
    pygame.display.set_caption("烟花服务器")

    # ========== 3. 创建游戏对象 ==========
    # 3.1 烟花管理器：负责管理所有烟花的创建、更新和绘制
    firework_manager = FireworkManager()

    # 3.2 开始界面：显示开始菜单，处理菜单事件
    start_screen = StartScreen()

    # 3.3 拖尾效果表面：创建一个半透明表面，用于实现烟花拖尾效果
    # SRCALPHA 表示支持透明度
    fade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    fade.fill(BLACK_ALPHA)  # 填充半透明黑色

    # ========== 4. 创建并启动Socket服务器 ==========
    # 创建服务器实例
    server = SimpleSocketServer()
    # 启动服务器，传入烟花管理器，这样服务器才能控制烟花
    server.start(firework_manager)

    # ========== 5. 游戏主循环 ==========
    # pygame游戏都需要一个主循环，不断处理事件和更新画面
    clock = pygame.time.Clock()  # 用于控制帧率
    running = True  # 控制主循环是否继续
    in_game = False  # 是否在游戏中（True表示已经开始游戏，False表示在开始菜单）

    # ----- 主循环开始 -----
    while running:
        # ========== 5.1 事件处理模块 ==========
        # pygame.event.get() 返回一个列表，包含所有待处理的事件
        for event in pygame.event.get():

            # ----- 5.1.1 处理窗口关闭事件 -----
            if event.type == pygame.QUIT:
                running = False  # 设置运行标志为False，退出循环

            # ----- 5.1.2 处理窗口大小改变事件 -----
            elif event.type == pygame.VIDEORESIZE:
                # 更新全局宽高变量
                WIDTH, HEIGHT = event.w, event.h
                # 重新创建窗口，保持可调整大小属性
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                # 重新创建拖尾表面，适应新窗口大小
                fade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                fade.fill(BLACK_ALPHA)

            # ----- 5.1.3 处理键盘按键事件 -----
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

            # ----- 5.1.4 处理开始界面的事件 -----
            # 只在非游戏状态处理开始界面事件
            if not in_game:
                # 将事件传递给开始界面处理（如按钮点击）
                if start_screen.handle_event(event):
                    # 如果开始界面返回True（点击了进入按钮），进入游戏
                    in_game = True

        # ========== 5.2 游戏状态更新模块 ==========
        if in_game:
            # ----- 5.2.1 更新所有烟花状态 -----
            # 包括：位置移动、速度变化、爆炸检测、粒子效果等
            firework_manager.update()

            # ========== 5.3 画面绘制模块 ==========
            # ----- 5.3.1 清空屏幕 -----
            # 用黑色填充整个屏幕，清除上一帧的内容
            screen.fill(BLACK)

            # ----- 5.3.2 绘制拖尾效果 -----
            # 在现有画面上覆盖一层半透明黑色
            # 这样之前的画面会逐渐变暗，产生烟花拖尾效果
            screen.blit(fade, (0, 0))

            # ----- 5.3.3 绘制所有烟花 -----
            # 包括未爆炸的烟花和爆炸后的粒子
            firework_manager.draw(screen)

            # ----- 5.3.4 显示提示信息（如果没有烟花）-----
            if firework_manager.get_firework_count() == 0:
                # 创建提示文本
                tip = start_screen.font_small.render(
                    "空格发射 | 服务器运行中",
                    True,
                    (100, 150, 255)
                )
                # 获取文本矩形并居中定位（底部居中）
                tip_rect = tip.get_rect(center=(WIDTH//2, HEIGHT-50))

                # 创建文本背景（半透明黑色框）
                bg = pygame.Surface((tip_rect.width+20, tip_rect.height+10))
                bg.fill((0, 0, 0))  # 填充黑色
                bg.set_alpha(100)    # 设置透明度为100/255

                # 绘制背景框
                screen.blit(bg, (tip_rect.x-10, tip_rect.y-5))
                # 绘制文本
                screen.blit(tip, tip_rect)

        else:
            # ========== 5.4 菜单界面处理 ==========
            # ----- 5.4.1 更新开始界面动画 -----
            start_screen.update()
            # ----- 5.4.2 绘制开始界面 -----
            start_screen.draw(screen)

        # ========== 5.5 显示更新模块 ==========
        # pygame.display.flip() 将所有绘制的内容显示到屏幕上
        # 这是双缓冲技术，可以避免画面闪烁
        pygame.display.flip()

        # ========== 5.6 控制帧率 ==========
        # clock.tick(60) 控制游戏帧率为60帧/秒
        # 这样可以限制CPU使用率，并保持动画流畅
        clock.tick(60)

    # ========== 6. 程序退出清理 ==========
    # ----- 6.1 关闭Socket服务器 -----
    server.stop()

    # ----- 6.2 退出pygame -----
    # 释放pygame占用的资源
    pygame.quit()

    # ----- 6.3 退出程序 -----
    sys.exit()


# ==================== 程序入口 ====================
# 如果直接运行这个文件（而不是被导入），则执行main()函数
if __name__ == "__main__":
    main()