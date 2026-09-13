import os
import time
import cv2
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import QLabel
from kivy.clock import Clock
from kivy.graphics.texture import Texture

# Конфигурация камеры и пути на внешнюю SD-карту
RTSP_URL = "rtsp://admin:L2B85342@192.168.0.161:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
SD_CARD_PATH = "/storage/0951-E53E/ImouRecords/"

class ImouClientApp(App):
    def build(self):
        self.title = "Imou Monitor & Recorder"
        self.mode = "motion" # "continuous" или "motion"
        self.last_frame = None
        self.motion_detected = False
        
        # Создаем папку на SD-карте
        if not os.path.exists(SD_CARD_PATH):
            try:
                os.makedirs(SD_CARD_PATH, exist_ok=True)
            except Exception as e:
                print(f"Ошибка создания папки на SD: {e}")

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Виджет видеопотока
        self.img_widget = Image(size_hint=(1, 0.7))
        layout.add_widget(self.img_widget)
        
        # Статусная строка
        self.status_label = QLabel(text="Статус: Подключение к камере...", size_hint=(1, 0.1), font_size=16)
        layout.add_widget(self.status_label)
        
        # Панель управления (переключатель режимов)
        btn_layout = BoxLayout(size_hint=(1, 0.2), spacing=10)
        self.mode_btn = Button(text="Режим: По движению", background_color=(0.2, 0.6, 0.8, 1))
        self.mode_btn.bind(on_press=self.toggle_mode)
        btn_layout.add_widget(self.mode_btn)
        layout.add_widget(btn_layout)
        
        # Запуск фонового потока захвата видео
        self.capture_thread = threading.Thread(target=self.rtsp_worker, daemon=True)
        self.capture_thread.start()
        
        Clock.schedule_interval(self.update_ui, 1.0 / 30.0)
        return layout

    def toggle_mode(self, instance):
        if self.mode == "motion":
            self.mode = "continuous"
            self.mode_btn.text = "Режим: Непрерывный"
        else:
            self.mode = "motion"
            self.mode_btn.text = "Режим: По движению"

    def rtsp_worker(self):
        cap = cv2.VideoCapture(RTSP_URL)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = None
        prev_gray = None
        recording_timer = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                time.sleep(2)
                cap.open(RTSP_URL)
                continue
                
            self.last_frame = frame
            
            # Программный детектор движения для режима "По движению"
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if prev_gray is not None:
                frame_diff = cv2.absdiff(prev_gray, gray)
                thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)
                cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                motion_found = any(cv2.contourArea(c) > 500 for c in cnts)
                if motion_found:
                    self.motion_detected = True
                    recording_timer = 150 # Писать еще 5 секунд после окончания движения
                else:
                    if recording_timer > 0:
                        recording_timer -= 1
                    else:
                        self.motion_detected = False

            prev_gray = gray
            
            # Логика записи в зависимости от выбранного режима
            should_record = (self.mode == "continuous") or (self.mode == "motion" and self.motion_detected)
            
            if should_record:
                if out is None:
                    filename = os.path.join(SD_CARD_PATH, f"rec_{int(time.time())}.mp4")
                    h, w, _ = frame.shape
                    out = cv2.VideoWriter(filename, fourcc, 20.0, (w, h))
                out.write(frame)
            else:
                if out is not None:
                    out.release()
                    out = None

            time.sleep(0.01)

    def update_ui(self, dt):
        if self.last_frame is not None:
            frame = cv2.flip(self.last_frame, 0)
            buf = frame.tostring()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.img_widget.texture = texture
            
            status_text = f"Режим: {'Цикличный' if self.mode == 'continuous' else 'По движению'} | "
            status_text += f"Запись идет ({'Движение!' if self.motion_detected else 'Ожидание'})" if (self.mode=='continuous' or self.motion_detected) else "Режим ожидания"
            self.status_label.text = status_text

if __name__ == '__main__':
    ImouClientApp().run()