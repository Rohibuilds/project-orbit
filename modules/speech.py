import queue
import threading

class SpeechEngine:
    def __init__(self, rate=165, enabled=True):
        self.rate = rate
        self.enabled = enabled
        self.speaking = threading.Event()
        self.jobs = queue.Queue(maxsize=16)
        self.recognizer = None
        self.sr = None
        if enabled:
            try:
                import speech_recognition as sr
                self.sr = sr
                self.recognizer = sr.Recognizer()
            except ImportError:
                print("Voice input unavailable; typed dashboard commands still work.")
            threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
        except Exception as exc:
            print(f"Speech output unavailable: {exc}")
            engine = None
        while True:
            text = self.jobs.get()
            try:
                if engine:
                    self.speaking.set()
                    engine.say(text)
                    engine.runAndWait()
            except Exception as exc:
                print(f"Speech output error: {exc}")
            finally:
                self.speaking.clear()
                self.jobs.task_done()

    def speak(self, text):
        text = str(text).strip()
        if not text:
            return
        print(f"ORBIT: {text}")
        if self.enabled:
            try:
                self.jobs.put_nowait(text)
            except queue.Full:
                print("Speech queue full; reply remains visible on dashboard.")

    def listen_once(self, timeout=5, phrase_time_limit=8):
        if not self.recognizer or self.speaking.is_set() or not self.jobs.empty():
            return None
        try:
            with self.sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            if self.speaking.is_set():
                return None
            return self.recognizer.recognize_google(audio).strip()
        except (self.sr.WaitTimeoutError, self.sr.UnknownValueError):
            return None
        except Exception as exc:
            print(f"Voice input unavailable: {exc}")
            return None
