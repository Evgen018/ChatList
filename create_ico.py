"""
Скрипт для создания иконки приложения ChatList.
Генерирует иконку с красной звездой в голубом круге.
"""

from PIL import Image, ImageDraw
import math
import os


def draw_star(draw, center_x: int, center_y: int, outer_radius: int, inner_radius: int, 
              points: int = 5, color: tuple = (220, 50, 50), rotation: float = -90):
    """
    Рисует звезду.
    
    Args:
        draw: ImageDraw объект
        center_x, center_y: Центр звезды
        outer_radius: Внешний радиус (до вершин)
        inner_radius: Внутренний радиус (до впадин)
        points: Количество лучей
        color: Цвет заливки
        rotation: Угол поворота в градусах (-90 для вершины вверх)
    """
    vertices = []
    
    for i in range(points * 2):
        # Чередуем внешний и внутренний радиус
        radius = outer_radius if i % 2 == 0 else inner_radius
        # Угол для текущей вершины
        angle = math.radians(rotation + (i * 180 / points))
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        vertices.append((x, y))
    
    draw.polygon(vertices, fill=color)


def create_chatlist_icon(output_path: str = "app.ico"):
    """
    Создаёт иконку приложения с красной звездой в голубом круге.
    
    Args:
        output_path: Путь для сохранения иконки
    """
    # Размеры иконок для ICO файла
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    
    # Цвета
    background_color = (0, 0, 0, 0)  # Прозрачный фон
    circle_color = (100, 180, 255)  # Голубой цвет круга
    star_color = (220, 50, 50)  # Красный цвет звезды
    
    images = []
    
    for size in sizes:
        width, height = size
        
        # Создаём изображение с прозрачным фоном
        img = Image.new('RGBA', (width, height), background_color)
        draw = ImageDraw.Draw(img)
        
        # Центр и радиус круга
        center_x = width // 2
        center_y = height // 2
        
        # Отступ для круга (чтобы он вписывался в квадрат)
        padding = int(min(width, height) * 0.05)
        circle_radius = min(width, height) // 2 - padding
        
        # Рисуем голубой круг
        circle_bbox = [
            center_x - circle_radius,
            center_y - circle_radius,
            center_x + circle_radius,
            center_y + circle_radius
        ]
        draw.ellipse(circle_bbox, fill=circle_color)
        
        # Параметры звезды
        # Размеры звезды относительно радиуса круга (лучи касаются края)
        outer_radius = int(circle_radius * 0.95)
        inner_radius = int(outer_radius * 0.38)  # Соотношение для классической 5-конечной звезды
        
        # Рисуем красную звезду
        draw_star(
            draw, 
            center_x, 
            center_y, 
            outer_radius, 
            inner_radius, 
            points=5, 
            color=star_color,
            rotation=-90  # Вершина направлена вверх
        )
        
        images.append(img)
    
    # Сохраняем все размеры в один ICO файл
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )
    
    print(f"Иконка успешно создана: {output_path}")
    print(f"Размеры: {[f'{s[0]}x{s[1]}' for s in sizes]}")


if __name__ == "__main__":
    # Создаём иконку в текущей директории
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "app.ico")
    
    create_chatlist_icon(icon_path)
