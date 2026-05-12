
# Проектная работа по Object Detection

### Поиск яблок, огурцов, помидоров на изображении

# О модели

### yolo11s на 100 эпохах (~4 часа)
### Датасет содержал более 7000 изображений, включая и негативные примеры
## [Блокнот](https://colab.research.google.com/drive/1Lz63sQ9nS10Gul4gbbhQq0HPdUx6qAqZ?usp=sharing) с обучением

# Демо
## [Сайт](fruitdet.ru) + [Telegram бот](t.me/FruitDetBot)  (Запущены до 02.06.2026)

# Запуск (с Caddy)

### env struct:
```bash
TELEGRAM_TOKEN=...
```

### запуск:
```bash
docker compose up --build
```
