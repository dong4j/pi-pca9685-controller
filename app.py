from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import Adafruit_PCA9685
import time
import threading
import math
from concurrent.futures import ThreadPoolExecutor
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # 允许所有来源的跨域请求

# 初始化 PCA9685
pwm = Adafruit_PCA9685.PCA9685()

# 配置舵机的最小和最大脉冲长度
servo_min = 150
servo_max = 600
step_size = 5  # 增加步长，但保持相对小的值
update_frequency = 100  # Hz，进一步增加更新频率
move_duration = 0.05  # 秒，减少单次移动的持续时间

# 设置频率为 60Hz
pwm.set_pwm_freq(60)

# 初始化舵机位置
servo0_position = 375
servo1_position = 445

# 创建一个锁来保护共享资源
lock = threading.Lock()

# 创建一个事件来控制连续调整
continuous_event = threading.Event()

# 更新舵机位置的函数
def update_servo(channel, position):
    pwm.set_pwm(channel, 0, position)

# 初始化舵机的函数
def initialize_servos():
    global servo0_position, servo1_position
    with lock:
        update_servo(0, servo0_position)
        update_servo(1, servo1_position)
    print("舵机已初始化到中间位置")

# 平滑移动函数
def smooth_move(channel, start, end, duration):
    steps = int(duration * update_frequency)
    for i in range(steps):
        t = i / steps
        # 使用平方函数来创建更快但仍然平滑的加速和减速效果
        smooth_t = t * t * (3 - 2 * t)
        position = int(start + (end - start) * smooth_t)
        update_servo(channel, position)
        time.sleep(1 / update_frequency)

# 调整舵机的函数
def adjust_servo(direction):
    global servo0_position, servo1_position
    with lock:
        if direction == 'left':
            target = max(servo_min, servo0_position + step_size)
            smooth_move(0, servo0_position, target, move_duration)
            servo0_position = target
        elif direction == 'right':
            target = min(servo_max, servo0_position - step_size)
            smooth_move(0, servo0_position, target, move_duration)
            servo0_position = target
        elif direction == 'up':
            target = max(servo_min, servo1_position - step_size)
            smooth_move(1, servo1_position, target, move_duration)
            servo1_position = target
        elif direction == 'down':
            target = min(servo_max, servo1_position + step_size)
            smooth_move(1, servo1_position, target, move_duration)
            servo1_position = target
    return servo0_position, servo1_position

def continuous_adjust(direction):
    while not continuous_event.is_set():
        adjust_servo(direction)

def reset_servos():
    with lock:
        update_servo(0, 375)
        update_servo(1, 445)
    print("舵机已重置到中间位置")
    return 375, 445

# 新增：处理摇杆输入的函数
def handle_joystick(horizontal, vertical, last_servo0, last_servo1):
    global servo0_position, servo1_position
    
    # 使用上次记录的位置作为起始点
    servo0_position = last_servo0
    servo1_position = last_servo1
    
    # 计算移动距离
    distance = math.sqrt(horizontal**2 + vertical**2)
    
    # 如果移动距离太小，保持当前位置
    if distance < 0.1:
        return servo0_position, servo1_position
    
    # 计算水平和垂直方向的移动量
    horizontal_move = int(horizontal * step_size * 2)
    vertical_move = int(vertical * step_size * 2)
    
    with lock:
        # 更新水平舵机位置
        new_servo0 = max(servo_min, min(servo_max, servo0_position + horizontal_move))
        smooth_move(0, servo0_position, new_servo0, move_duration)
        servo0_position = new_servo0
        
        # 更新垂直舵机位置
        new_servo1 = max(servo_min, min(servo_max, servo1_position - vertical_move))
        smooth_move(1, servo1_position, new_servo1, move_duration)
        servo1_position = new_servo1
    
    return servo0_position, servo1_position

def get_video_type(url):
    """
    根据 URL 确定视频类型
    """
    if re.search(r'\.flv($|\?)', url):
        return 'flv'
    elif re.search(r'\.m3u8($|\?)', url):
        return 'm3u8'
    elif re.search(r'\.mp4($|\?)', url):
        return 'mp4'
    else:
        # 如果无法确定，可以返回一个默认值或者 None
        return None

@app.route('/')
def index():
    video_url = "http://192.168.21.7:9090/pi5a/0.live.mp4"  # 从配置或数据库获取
    video_type = get_video_type(video_url)
    
    if video_type is None:
        # 或者返回错误
        return "无法确定视频类型", 400
    
    return render_template('index.html', video_url=video_url, video_type=video_type)

@app.route('/control', methods=['POST'])
def control():
    direction = request.json['direction']
    action = request.json['action']  # 'single', 'start', 或 'stop'
    
    if action == 'single':
        servo0, servo1 = adjust_servo(direction)
    elif action == 'start':
        continuous_event.clear()
        threading.Thread(target=continuous_adjust, args=(direction,), daemon=True).start()
        servo0, servo1 = servo0_position, servo1_position
    else:  # 'stop'
        continuous_event.set()
        servo0, servo1 = servo0_position, servo1_position
    
    return jsonify({
        'servo0': servo0,
        'servo1': servo1
    })

@app.route('/reset', methods=['POST'])
def reset():
    servo0, servo1 = reset_servos()
    return jsonify({
        'servo0': servo0,
        'servo1': servo1
    })

@app.route('/joystick-control', methods=['POST'])
def joystick_control():
    data = request.json
    horizontal = data['horizontal']
    vertical = data['vertical']
    last_servo0 = data['lastServo0']
    last_servo1 = data['lastServo1']
    
    servo0, servo1 = handle_joystick(horizontal, vertical, last_servo0, last_servo1)
    
    return jsonify({
        'servo0': servo0,
        'servo1': servo1
    })

@app.after_request
def add_security_headers(response):
    # 完全禁用 CSP
    response.headers['Content-Security-Policy'] = "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;"
    
    # CORS headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    return response

if __name__ == '__main__':
    # 在启动服务器之前初始化舵机
    initialize_servos()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
