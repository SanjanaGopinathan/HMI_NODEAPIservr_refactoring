import cv2
import time
import threading
import logging
from typing import Dict, Optional, Generator

logger = logging.getLogger(__name__)

class StreamManager:
    """
    Manages OpenCV VideoCaptures for RTSP streams.
    Implements a singleton-like pattern to share streams if needed, 
    but for simplicity, we will open a new capture per request or use a generator.
    
    Actually, for MJPEG streaming to multiple clients, we should ideally share the frame reading thread.
    """
    _instances: Dict[str, 'CameraStream'] = {}
    _lock = threading.Lock()

    @classmethod
    def get_stream(cls, camera_id: str, rtsp_url: str):
        with cls._lock:
            if camera_id not in cls._instances:
                cls._instances[camera_id] = CameraStream(camera_id, rtsp_url)
            stream = cls._instances[camera_id]
            stream.add_client()
            return stream

    @classmethod
    def release_stream(cls, camera_id: str):
        with cls._lock:
             if camera_id in cls._instances:
                stream = cls._instances[camera_id]
                stream.remove_client()

class CameraStream:
    def __init__(self, camera_id: str, rtsp_url: str):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.cap = None
        self.last_frame = None
        self.is_running = False
        self.lock = threading.Lock()
        self.last_access = time.time()
        self.thread = None
        self.client_count = 0

    def add_client(self):
        with self.lock:
            self.client_count += 1
            logger.info(f"Client connected to {self.camera_id}. Count: {self.client_count}")

    def remove_client(self):
        with self.lock:
            self.client_count -= 1
            logger.info(f"Client disconnected from {self.camera_id}. Count: {self.client_count}")
            if self.client_count <= 0:
                self.stop()

    def start(self):
        if self.is_running:
            return
        
        self.cap = cv2.VideoCapture(self.rtsp_url)
        if not self.cap.isOpened():
            logger.error(f"Failed to open stream for {self.camera_id}: {self.rtsp_url}")
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        logger.info(f"Started stream for {self.camera_id}")

    def _update(self):
        while self.is_running:
            # Still keep timeout as fallback in case ref counting fails
            if time.time() - self.last_access > 30 and self.client_count <= 0:
                logger.info(f"Stream timeout for {self.camera_id}")
                self.stop()
                break

            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.last_frame = frame
                else:
                    # Reconnect logic could go here
                    time.sleep(1)
            else:
                time.sleep(1)
            time.sleep(0.01) # Max 100fps poll

    def get_frame(self):
        self.last_access = time.time()
        with self.lock:
            if self.last_frame is None:
                return None
            
            # Encde to JPEG
            ret, buffer = cv2.imencode('.jpg', self.last_frame)
            if ret:
                return buffer.tobytes()
            return None

    def stop(self):
        # Already stopped?
        if not self.is_running:
            return

        self.is_running = False
        # Do not join thread from within the thread itself if called from _update
        if self.thread and threading.current_thread() != self.thread:
            self.thread.join(timeout=1.0)
        
        if self.cap:
            self.cap.release()
        
        # Remove self from global manager
        # Need to be careful with lock re-entrancy if called from remove_client which holds lock?
        # remove_client holds instance lock. stop() logic needs access to Global manager lock.
        # This is safe as long as we don't hold Global lock when calling remove_client.
        
        # However, remove_client is called from StreamManager.release_stream which holds Global lock?
        # Wait, release_stream holds Global lock. So we are inside Global lock.
        # Then inside remove_client we take instance lock.
        # Then we call stop().
        # Inside stop(), we try to take Global lock to remove from _instances. -> DEADLOCK.
        
        # FIX: stop() should not try to remove from _instances if called from release_stream.
        # Actually, let's keep it simple: StreamManager manages _instances removal.
        # But here stop() accesses StreamManager._instances.
        
        # To avoid deadlock:
        # StreamManager.release_stream shouldn't call remove_client while holding global lock?
        # Or I move the deletion logic.
        
        pass 

    def _cleanup_resources(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        logger.info(f"Resources released for {self.camera_id}")

    def stop(self):
        self.is_running = False
        # We spawn a thread to cleanup to avoid blocking or deadlocks
        threading.Thread(target=self._cleanup_resources).start()
        
        # Remove self from global manager - this might need safety
        # We will let StreamManager handle removal if count is 0
        # But we need to remove it from dict.
        # Let's do it in a non-locking way or minimal way.
        
        # Ideally: remove_client returns True if stopped. StreamManager deletes it.
        pass

# Redefining stop to be simple and safe
    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        logger.info(f"Stopped stream for {self.camera_id}")

def generate_frames(camera_id: str, rtsp_url: str) -> Generator[bytes, None, None]:
    """
    Generator function for FastAPI StreamingResponse
    """
    stream = StreamManager.get_stream(camera_id, rtsp_url)
    stream.start()

    try:
        while stream.is_running:
            frame_bytes = stream.get_frame()
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # Wait for stream to initialize
                time.sleep(0.1)
            
            time.sleep(0.04) # Limit to ~25fps delivery
    except GeneratorExit:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error streaming: {e}")
    finally:
        StreamManager.release_stream(camera_id)
