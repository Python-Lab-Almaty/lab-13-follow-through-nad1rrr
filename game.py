import turtle
import random
import time
import hashlib
import os
import json

# ----------------------------
# 🟢 КОНСТАНТЫ
# ----------------------------
WIDTH, HEIGHT = 1400, 900

# 🟢 ИНИЦИАЛИЗАЦИЯ ЛОГА
log = []

# ----------------------------
# 🟢 ПОЛУЧЕНИЕ ИМЕНИ СТУДЕНТА
# ----------------------------
def get_student_name():
    """Запрашивает имя студента"""
    screen = turtle.Screen()
    name = screen.textinput("Student Name", "Enter your name:")
    if not name or name.strip() == "":
        name = "anonymous"
    return name.strip().lower()

# ----------------------------
# 🟢 СОХРАНЕНИЕ/ЗАГРУЗКА ПОЗИЦИЙ
# ----------------------------
def get_positions_file(name):
    """Возвращает путь к файлу сохранения позиций"""
    return f"mission_positions_{name}.json"

def load_or_create_positions(name):
    """Загружает или создаёт новые позиции на основе имени"""
    filename = get_positions_file(name)
    
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Загружена сохранённая сессия для {name}")
            return tuple(data['start']), tuple(data['goal']), data['obstacles']
    
    name_hash = hashlib.md5(name.encode()).hexdigest()
    seed = int(name_hash[:8], 16) % 10000
    random.seed(seed)
    
    corners = [(-550, -350), (550, 350), (-550, 350), (550, -350)]
    diagonal_pairs = [(0, 1), (2, 3)]
    pair_index = seed % 2
    start_idx, goal_idx = diagonal_pairs[pair_index]
    
    start = corners[start_idx]
    goal = corners[goal_idx]
    
    obstacles = []
    sizes = [(60, 150), (150, 60), (100, 100), (80, 200), (200, 80), (120, 120)]
    
    for i in range(8):
        while True:
            x = random.randint(-450, 450)
            y = random.randint(-280, 280)
            size = random.choice(sizes)
            
            if abs(x - start[0]) > 120 or abs(y - start[1]) > 120:
                if abs(x - goal[0]) > 120 or abs(y - goal[1]) > 120:
                    overlap = False
                    for ox, oy, obs_size in obstacles:
                        if abs(x - ox) < 150 and abs(y - oy) < 150:
                            overlap = True
                            break
                    
                    if not overlap:
                        obstacles.append((x, y, size))
                        break
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'start': start,
            'goal': goal,
            'obstacles': obstacles,
            'name': name
        }, f, indent=2)
    
    print(f"🎯 Создана новая сессия для {name} (seed: {seed})")
    return start, goal, obstacles

def clear_session(name):
    """Удаляет сохранённую сессию"""
    filename = get_positions_file(name)
    if os.path.exists(filename):
        os.remove(filename)
        print(f"🗑️ Сессия {name} удалена")

# ----------------------------
# 🟢 ФУНКЦИЯ СОХРАНЕНИЯ ЛОГА (ОДИН ФАЙЛ!)
# ----------------------------
def save_log(reason="end"):
    """Сохраняет ВСЕ логи в ОДИН файл (перезаписывает старый)"""
    global log, student_name, start, goal, impassable_obstacles, steps, penalties
    
    try:
        # 🟢 ОДИН файл на студента (всегда перезаписывается!)
        filename = f"log_{student_name}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "name": student_name,
                "start": start,
                "goal": goal,
                "obstacles": impassable_obstacles,
                "reason": reason,
                "log": log,  # Все события в одном массиве
                "total_steps": steps,
                "total_penalties": penalties,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "game_version": "1.0"
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Лог сохранён: {filename} ({len(log)} записей)")
    except Exception as e:
        print(f"❌ Ошибка сохранения лога: {e}")

# ----------------------------
# 🟢 ИНИЦИАЛИЗАЦИЯ ИГРЫ
# ----------------------------
student_name = get_student_name()
start, goal, impassable_obstacles = load_or_create_positions(student_name)

# ----------------------------
# 🟢 ЭКРАН
# ----------------------------
screen = turtle.Screen()
screen.setup(WIDTH, HEIGHT)
screen.title(f"Red Riding Hood Mission - {student_name}")
screen.bgcolor("white")
screen.tracer(0)

# ----------------------------
# 🟢 ГЕРОЙ
# ----------------------------
hero = turtle.Turtle()
hero.shape("circle")
hero.color("red")
hero.penup()
hero.goto(start)
hero.shapesize(2, 2)

# ----------------------------
# 🟢 ПРЕПЯТСТВИЯ
# ----------------------------
dynamic_obstacles = []

# ----------------------------
# 🟢 СЧЁТ
# ----------------------------
steps = 0
penalties = 0

# ----------------------------
# 🟢 СКОРОСТЬ
# ----------------------------
vx = 3
vy = 3

# ----------------------------
# 🟢 РЕЖИМ
# ----------------------------
going_forward = True

# ----------------------------
# 🟢 ОТРИСОВКА
# ----------------------------
def draw_field_markers():
    """Рисует точки Start (A) и Finish (B)"""
    marker = turtle.Turtle()
    marker.hideturtle()
    marker.penup()
    
    marker.goto(start)
    marker.dot(50, "green")
    marker.goto(start[0], start[1] - 50)
    marker.write("A (Start)", align="center", font=("Arial", 16, "bold"))
    
    marker.goto(goal)
    marker.dot(50, "blue")
    marker.goto(goal[0], goal[1] - 50)
    marker.write("B (Finish)", align="center", font=("Arial", 16, "bold"))
    
    marker.goto(0, HEIGHT//2 - 60)
    marker.write(f"Student: {student_name}", align="center", font=("Arial", 14, "italic"))

def spawn_dynamic_obstacle():
    """Создаёт препятствие в случайном месте"""
    if going_forward:
        return
    
    spawn_side = random.choice(['top', 'left', 'right'])
    
    if spawn_side == 'top':
        x = random.randint(-500, 500)
        y = HEIGHT // 2 + 50
    elif spawn_side == 'left':
        x = -WIDTH // 2 - 50
        y = random.randint(-300, 300)
    else:
        x = WIDTH // 2 + 50
        y = random.randint(-300, 300)
    
    size = random.choice([(80, 80), (100, 60), (60, 100), (90, 90)])
    fall_speed = random.uniform(1.5, 3.0)
    final_y = random.randint(-200, 200)
    
    dynamic_obstacles.append([x, y, size[0], size[1], True, fall_speed, final_y])

def draw_all():
    """Рисует ВСЁ: статичные препятствия, динамические, героя, счёт"""
    if hasattr(draw_all, 'dynamic_drawers'):
        for drawer in draw_all.dynamic_drawers:
            drawer.clear()
    else:
        draw_all.dynamic_drawers = []
    
    if not hasattr(draw_all, 'static_drawn'):
        for ox, oy, (w, h) in impassable_obstacles:
            drawer = turtle.Turtle()
            drawer.hideturtle()
            drawer.penup()
            drawer.speed(0)
            drawer.goto(ox - w/2, oy - h/2)
            drawer.pendown()
            drawer.fillcolor("darkred")
            drawer.begin_fill()
            for _ in range(2):
                drawer.forward(w)
                drawer.left(90)
                drawer.forward(h)
                drawer.left(90)
            drawer.end_fill()
            drawer.penup()
        draw_all.static_drawn = True
    
    draw_all.dynamic_drawers = []
    for obs in dynamic_obstacles:
        x, y, w, h, is_falling, speed, final_y = obs
        drawer = turtle.Turtle()
        drawer.hideturtle()
        drawer.penup()
        drawer.speed(0)
        drawer.goto(x - w/2, y - h/2)
        drawer.pendown()
        drawer.fillcolor("darkgreen")
        drawer.begin_fill()
        for _ in range(2):
            drawer.forward(w)
            drawer.left(90)
            drawer.forward(h)
            drawer.left(90)
        drawer.end_fill()
        drawer.penup()
        draw_all.dynamic_drawers.append(drawer)
    
    if hasattr(draw_all, 'score_drawer'):
        draw_all.score_drawer.clear()
    else:
        draw_all.score_drawer = turtle.Turtle()
        draw_all.score_drawer.hideturtle()
        draw_all.score_drawer.penup()
    
    score_drawer = draw_all.score_drawer
    score_drawer.goto(0, -HEIGHT//2 + 40)
    score = steps - penalties
    score_drawer.clear()
    score_drawer.write(f"Steps: {steps} | Penalties: {penalties} | Score: {score}",
                       align="center", font=("Arial", 16, "bold"))
    
    screen.update()

def rect_collision(hero_x, hero_y, rect_x, rect_y, rect_w, rect_h, hero_radius=15):
    """Проверяет столкновение круга с прямоугольником"""
    closest_x = max(rect_x - rect_w/2, min(hero_x, rect_x + rect_w/2))
    closest_y = max(rect_y - rect_h/2, min(hero_y, rect_y + rect_h/2))
    distance_x = hero_x - closest_x
    distance_y = hero_y - closest_y
    distance = (distance_x**2 + distance_y**2) ** 0.5
    return distance < hero_radius

def check_collision():
    """Проверяет столкновения"""
    global penalties
    for ox, oy, (w, h) in impassable_obstacles:
        if rect_collision(hero.xcor(), hero.ycor(), ox, oy, w, h, hero_radius=15):
            penalties += 10
            print(f"⚠️ ШТРАФ! (-10 баллов)")
            hero.goto(hero.xcor() - vx*3, hero.ycor() - vy*3)
            return "penalty"
    
    for obs in dynamic_obstacles:
        x, y, w, h, is_falling, speed, final_y = obs
        if rect_collision(hero.xcor(), hero.ycor(), x, y, w, h, hero_radius=15):
            return "game_over"
    
    return "ok"

# ----------------------------
# 🟢 УПРАВЛЕНИЕ (БЕЗ ЧЕКПОИНТОВ!)
# ----------------------------
def up():
    global steps
    hero.sety(hero.ycor() + vy)
    steps += 1
    
    log.append({
        "event": "move",
        "direction": "up",
        "x": hero.xcor(),
        "y": hero.ycor(),
        "time": time.time()
    })

def down():
    global steps
    hero.sety(hero.ycor() - vy)
    steps += 1
    
    log.append({
        "event": "move",
        "direction": "down",
        "x": hero.xcor(),
        "y": hero.ycor(),
        "time": time.time()
    })

def left():
    global steps
    hero.setx(hero.xcor() - vx)
    steps += 1
    
    log.append({
        "event": "move",
        "direction": "left",
        "x": hero.xcor(),
        "y": hero.ycor(),
        "time": time.time()
    })

def right():
    global steps
    hero.setx(hero.xcor() + vx)
    steps += 1
    
    log.append({
        "event": "move",
        "direction": "right",
        "x": hero.xcor(),
        "y": hero.ycor(),
        "time": time.time()
    })

def reset_session():
    clear_session(student_name)
    print("🔄 Сессия сброшена. Перезапустите игру.")

screen.listen()
screen.onkey(up, "Up")
screen.onkey(down, "Down")
screen.onkey(left, "Left")
screen.onkey(right, "Right")
screen.onkey(up, "w")
screen.onkey(down, "s")
screen.onkey(left, "a")
screen.onkey(right, "d")
screen.onkey(reset_session, "r")

# ----------------------------
# 🟢 ОСНОВНОЙ ЦИКЛ
# ----------------------------
draw_field_markers()
screen.update()

obstacles_spawned_count = 0
start_time = time.time()

# 🟢 ЛОГИРОВАНИЕ СТАРТА
log.append({
    "event": "game_start",
    "x": hero.xcor(),
    "y": hero.ycor(),
    "time": time.time()
})

print(f"\n🎮 ИГРА ЗАПУЩЕНА")
print(f"👤 Студент: {student_name}")
print(f"📍 Start: {start}")
print(f"🎯 Goal: {goal}")
print(f"⚠️ Препятствий: {len(impassable_obstacles)}")
print(f"\n🎯 Цель: A → B → A")
print(f"⌨️ Управление: стрелки или WASD")
print(f"🔄 Сброс: R")
print(f"\n🔴 КРАСНЫЕ = штраф -10")
print(f"🟢 ЗЕЛЁНЫЕ = GAME OVER (появляются на обратном пути)")

while True:
    # 🟢 ФАЗА 2: На обратном пути
    if not going_forward:
        spawn_chance = 0.02 + (vx + vy) / 60
        
        if random.random() < spawn_chance and len(dynamic_obstacles) < 15:
            spawn_dynamic_obstacle()
            obstacles_spawned_count += 1
        
        for obs in dynamic_obstacles:
            if obs[4]:
                if obs[1] > obs[6]:
                    obs[1] -= obs[5]
                else:
                    obs[4] = False
    
    # Проверка достижения цели
    if going_forward and abs(hero.xcor() - goal[0]) < 40 and abs(hero.ycor() - goal[1]) < 40:
        print("🎯 Reached B! RETURN TO A!")
        print(f"🟢 Теперь будут появляться препятствия!")
        going_forward = False
        
        log.append({
            "event": "reached_goal_B",
            "x": hero.xcor(),
            "y": hero.ycor(),
            "time": time.time()
        })
    
    # Проверка возвращения
    if not going_forward and abs(hero.xcor() - start[0]) < 40 and abs(hero.ycor() - start[1]) < 40:
        total_time = time.time() - start_time
        final_score = steps - penalties
        print(f"\n🏆 MISSION COMPLETE!")
        print(f"⏱️ Time: {total_time:.2f} seconds")
        print(f"👣 Steps: {steps}")
        print(f"⚠️ Penalties: {penalties}")
        print(f"📊 Final Score: {final_score}")
        print(f"🟩 Препятствий появилось: {obstacles_spawned_count}")
        
        log.append({
            "event": "mission_complete",
            "x": hero.xcor(),
            "y": hero.ycor(),
            "time": time.time(),
            "score": final_score
        })
        
        with open(f"mission_records_{student_name}.json", 'w', encoding='utf-8') as f:
            json.dump({
                'score': final_score,
                'time': total_time,
                'steps': steps,
                'date': time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
        
        save_log("mission_complete")  # ✅ ОДИН РАЗ В КОНЦЕ!
        break
    
    # Столкновение
    collision = check_collision()
    if collision == "game_over":
        print("💥 GAME OVER!")
        print(f"🟩 Препятствий: {obstacles_spawned_count}")
        
        log.append({
            "event": "game_over",
            "x": hero.xcor(),
            "y": hero.ycor(),
            "time": time.time()
        })
        
        save_log("game_over")  # ✅ ОДИН РАЗ ПРИ GAME OVER!
        break
    
    draw_all()
    time.sleep(0.03)

turtle.done()
