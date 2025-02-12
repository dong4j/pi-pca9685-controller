from __future__ import division
import time
import keyboard  # 导入 keyboard 模块
import Adafruit_PCA9685

# 初始化 PCA9685
pwm = Adafruit_PCA9685.PCA9685()

# 配置舵机的最小和最大脉冲长度
servo_min = 150  # Min pulse length out of 4096
servo_max = 600  # Max pulse length out of 4096
step_size = 10   # 每次调整的脉冲变化量

# 设置频率为 60Hz
pwm.set_pwm_freq(60)

# 初始化舵机位置
servo0_position = (servo_min + servo_max) // 2
servo1_position = (servo_min + servo_max) // 2

# 更新舵机位置的函数
def update_servo(channel, position):
    pwm.set_pwm(channel, 0, position)

# 主循环，检测键盘输入
print('使用WSAD控制两个舵机，按下 Ctrl-C 退出程序')

try:
    while True:
        # 检查是否按下 A 键
        if keyboard.is_pressed('a'):
            servo0_position = max(servo_min, servo0_position - step_size)
            update_servo(0, servo0_position)
            print("按下 A 键，0 号舵机位置:", servo0_position)
            time.sleep(0.05)  # 调整响应速度

        # 检查是否按下 D 键
        elif keyboard.is_pressed('d'):
            servo0_position = min(servo_max, servo0_position + step_size)
            update_servo(0, servo0_position)
            print("按下 D 键，0 号舵机位置:", servo0_position)
            time.sleep(0.05)

        # 检查是否按下 W 键
        if keyboard.is_pressed('w'):
            servo1_position = max(servo_min, servo1_position - step_size)
            update_servo(1, servo1_position)
            print("按下 W 键，1 号舵机位置:", servo1_position)
            time.sleep(0.05)

        # 检查是否按下 S 键
        elif keyboard.is_pressed('s'):
            servo1_position = min(servo_max, servo1_position + step_size)
            update_servo(1, servo1_position)
            print("按下 S 键，1 号舵机位置:", servo1_position)
            time.sleep(0.05)

except KeyboardInterrupt:
    print("程序已退出")
