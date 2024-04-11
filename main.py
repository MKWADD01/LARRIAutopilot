# higher_level_concurrent_script.py
import subprocess
import multiprocessing
import os

def run_webcam_zones():
    # Change working directory to where WebcamZones.py is located
    #os.chdir("C:/Users/Adhi Ramkumar/LARRIAutopilot")
    os.chdir("C:/Users/User/PycharmProjects/LARRIAutopilot")
    # Run WebcamZones.py script
    subprocess.run(["python", "zones.py"])

def run_detect():
    # Change working directory to where detect.py is located
    #os.chdir("C:/Users/Adhi Ramkumar/LARRIAutopilot/yolov5/yolov5")
    os.chdir("C:/Users/User/PycharmProjects/LARRIAutopilot/yolov5")
    # Run detect.py script
    subprocess.run(["python", "detect.py", "--source", "0"])

if __name__ == "__main__":
    # Create processes for running WebcamZones.py and detect.py concurrently
    webcam_zones_process = multiprocessing.Process(target=run_webcam_zones)
    detect_process = multiprocessing.Process(target=run_detect)

    # Start both processes
    webcam_zones_process.start()
    detect_process.start()

    # Wait for both processes to finish
    webcam_zones_process.join()
    detect_process.join()

