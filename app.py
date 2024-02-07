from flask import Flask
from flask import render_template
from flask import Response
import sys
sys.path.insert(0, '/data/openpilot/system/camerad/snapshot')
import snapshot as sns
from time import sleep, time
import numpy as np
from threading import Event, Thread
from PIL import Image
import io
import cereal.messaging as messaging
from cereal.visionipc import VisionIpcClient, VisionStreamType
from common.realtime import DT_MDL

VISION_STREAMS = {
    "roadCameraState": VisionStreamType.VISION_STREAM_ROAD,
    "driverCameraState": VisionStreamType.VISION_STREAM_DRIVER,
    "wideRoadCameraState": VisionStreamType.VISION_STREAM_WIDE_ROAD,
}

def yuv_to_rgb(y, u, v):
  ul = np.repeat(np.repeat(u, 2).reshape(u.shape[0], y.shape[1]), 2, axis=0).reshape(y.shape)
  vl = np.repeat(np.repeat(v, 2).reshape(v.shape[0], y.shape[1]), 2, axis=0).reshape(y.shape)
  yuv = np.dstack((y, ul, vl)).astype(np.int16)
  yuv[:, :, 1:] -= 128
  m = np.array([
    [1.00000,  1.00000, 1.00000],
    [0.00000, -0.39465, 2.03211],
    [1.13983, -0.58060, 0.00000],
  ])
  rgb = np.dot(yuv, m).clip(0, 255)
  return rgb.astype(np.uint8)


def extract_image(buf, w, h, stride, uv_offset):
  y = np.array(buf[:uv_offset], dtype=np.uint8).reshape((-1, stride))[:h, :w]
  #u = np.array(buf[uv_offset::2], dtype=np.uint8).reshape((-1, stride//2))[:h//2, :w//2]
  #v = np.array(buf[uv_offset+1::2], dtype=np.uint8).reshape((-1, stride//2))[:h//2, :w//2]
  return y

def get_camera_data():
  fpic, pic  = sns.get_snapshots()
  if pic is not None:
    sns.jpeg_write("back.jpg", pic)
  if fpic is not None:
    #sns.jpeg_write("front.jpg", fpic)
    pass
  else:
    print("Error Taking Picture")

# This gets the acutal data off of the cameras. I have it set so that we only get
# the balck and white data to save processing time.
def get_cam_bytes(frame="roadCameraState", front_frame="driverCameraState"):
    sockets = [s for s in (frame, front_frame) if s is not None]
    sm = messaging.SubMaster(sockets)
    vipc_clients = {s: VisionIpcClient("camerad", VISION_STREAMS[s], True) for s in sockets}
    while sm[sockets[0]].frameId < int(4. / DT_MDL):
       sm.update()
    for client in vipc_clients.values():
      client.connect(True)
    # grab images
    rear, front = None, None
    if frame is not None:
        c = vipc_clients[frame]
        rear = extract_image(c.recv(), c.width, c.height, c.stride, c.uv_offset)
    if front_frame is not None:
        c = vipc_clients[front_frame]
        front = extract_image(c.recv(), c.width, c.height, c.stride, c.uv_offset)
    return rear, front

class ImageLoader:
    def __init__(self, frequency):
        self.frequency = frequency

        self.stop = Event()
        self.image = None
        self.fimage = None

        self.thread = Thread(target=self.worker)
        self.thread.start()
    
    #This gets the camera bytes and stores it in the image once every 60 seconds
    def worker(self):
        while not self.stop.is_set():
            # Get current image in separate thread
            i = int(time()) % 3
            fpic_arr, pic_arr = get_cam_bytes("roadCameraState", None)
            #pic_arr = np.array(pic)
            #fpic_arr = np.array(fpic)
            fpic_img = Image.fromarray(fpic_arr)
            #fpic_img = fpic_img.resize((640,640))
            #pic_img = Image.fromarray(pic_arr)
            #pic_img = pic_img.resize((640, 640))
            #new_img = Image.new("RGB", (1280, 640), 'white')
            #new_img.paste(pic_img, (0,0))
            #new_img.paste(fpic_img, (640,0))
            img_byte = io.BytesIO()
            #new_img.save(img_byte, format="jpeg")
            fpic_img.save(img_byte, format="jpeg")
            self.image = img_byte.getvalue()
            #self.image = np.array(pic)

            #with open("back.jpg", "rb") as f:
            #    self.image = f.read()
            #self.image = np.resize(self.image, (640, 640))
            sleep(1/self.frequency)


app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

def GetImage(frequency):
    imageLoader = ImageLoader(frequency)

    while True:
        image = imageLoader.image
        if image is not None:
          yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + image + b'\r\n')
        sleep(1/60)

@app.route("/stream")
def stream():
    # This streams the video. Maximum frame rate is 60FPS
    return Response(GetImage(60), mimetype = "multipart/x-mixed-replace; boundary=frame")

if(__name__ == "__main__"):
    app.run(debug = True, threaded = True, use_reloader = False, host="0.0.0.0", port=8080)
