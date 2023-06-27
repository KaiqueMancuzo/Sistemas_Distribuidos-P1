import zmq
import threading
import base64
import numpy as np
import cv2
import time
import socket
import pyaudio

text_init_port = 5000
text_port_range = 2
video_init_port = 5100
video_port_range = 2
audio_init_port = 5200
audio_port_range = 2
ips={"26.82.77.166","26.157.249.115"}

audio_format = pyaudio.paInt16  # Formato de áudio
audio_channels = 1  # Número de canais de áudio (1 para mono, 2 para estéreo)
audio_rate = 44100  # Taxa de amostragem em Hz
audio_chunk = 1024  # Tamanho do buffer de áudio
audio = pyaudio.PyAudio()


def text_subscriber_thread(ip,port):
    
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    
    subscriber.connect(f"tcp://{ip}:{text_init_port+port}")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    while True:
        message = subscriber.recv_string()
        print(message)

def video_subscriber_thread(ip,port):
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    
    subscriber.connect(f"tcp://{ip}:{video_init_port+port}")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    while True:
        stringcomp = subscriber.recv_string()
        nick, string = stringcomp.split(" ")
        frame = bytes(string,'utf-8')
        img = base64.b64decode(frame)
        numpy_img = np.frombuffer(img,dtype=np.uint8)
        source = cv2.imdecode(numpy_img,1)
        cv2.imshow(f"{nick}",source)
        cv2.waitKey(1)

def audio_subscriber_thread(ip,port):
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    subscriber.connect(f"tcp://{ip}:{audio_init_port+port}")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    stream = audio.open(
        format=audio_format,
        channels=audio_channels,
        rate=audio_rate,
        output=True
    )

    while True:
        audio_data = subscriber.recv()
        stream.write(audio_data)




def audio_publisher_thread(nick, ip):
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind_to_random_port(f"tcp://{ip}",min_port=audio_init_port,max_port=audio_init_port+video_port_range,max_tries=text_port_range)

    stream = audio.open(
        format=audio_format,
        channels=audio_channels,
        rate=audio_rate,
        input=True,
        frames_per_buffer=audio_chunk
    )

    while True:
        audio_data = stream.read(audio_chunk)
        publisher.send(audio_data)



def text_publisher_thread(nick, ip):
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind_to_random_port(f"tcp://{ip}",min_port=text_init_port,max_port=text_init_port+text_port_range,max_tries=text_port_range) 

    while True:
        message = input()
        message = f"[{nick}] :{message}"
        publisher.send_string(message)

def video_publisher_thread(nick, ip):
    camera = cv2.VideoCapture(0)
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind_to_random_port(f"tcp://{ip}",min_port=video_init_port,max_port=video_init_port+video_port_range,max_tries=video_port_range)
    while True:
        (grabbed, frame) = camera.read() 
        
        #frame = cv2.resize(frame,(640, 480))
        _,buffer = cv2.imencode('.jpg',frame)
        str_image = base64.b64encode(buffer).decode('utf-8')
        str_image = f"{nick}"+" "+str_image
        publisher.send_string(str_image)
        time.sleep(0.1)


def main():
    nick = input("Enter your nickname: ")
    nick = nick.split(" ")
    hostname=socket.gethostname()   
    IPAddr=socket.gethostbyname(hostname)   
    print("Your Computer Name is:"+hostname)   
    print("Your Computer IP Address is:"+IPAddr)
    for ip in ips:
        for port in range(text_port_range):
            text_sub_thread  = threading.Thread(target=text_subscriber_thread,args=(ip,port))
            video_sub_thread = threading.Thread(target=video_subscriber_thread,args=(ip,port))
            audio_sub_thread = threading.Thread(target=audio_subscriber_thread,args=(ip,port))
            text_sub_thread.start()
            video_sub_thread.start()
            audio_sub_thread.start()

    text_pub_thread  = threading.Thread(target=text_publisher_thread,args=(nick,IPAddr))
    video_pub_thread = threading.Thread(target=video_publisher_thread,args=(nick,IPAddr))
    audio_pub_thread = threading.Thread(target=audio_publisher_thread,args=(nick,IPAddr ))
   # text_pub_thread.start()
   # video_pub_thread.start()
   # audio_pub_thread.start()

if __name__ == "__main__":
    main()