import keyboard

print("按下 'Esc' 键退出")
while True:
    if keyboard.is_pressed('a'):
        print("A 键被按下")
    elif keyboard.is_pressed('d'):
        print("D 键被按下")
    elif keyboard.is_pressed('w'):
        print("W 键被按下")
    elif keyboard.is_pressed('s'):
        print("S 键被按下")
    elif keyboard.is_pressed('esc'):
        break
