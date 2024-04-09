import cv2

def run_webcam():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise IOError("Cannot open webcam")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        #dimensions of default camera(webcam)
        height, width = frame.shape[:2]

        #divides camera into 1/4's, 
        quarterWidth = width // 4
        threeQuarterWidth = 3 * quarterWidth

        cv2.line(frame, (quarterWidth, 0), (quarterWidth, height), (0, 0, 255), 2)  #First line at 1/4 width left zone
        cv2.line(frame, (threeQuarterWidth, 0), (threeQuarterWidth, height), (0, 0, 255), 2)  #Second line at 3/4 width, right zone

        cv2.imshow('Left, Center, Right zones', frame)

        #Exit webcam loop with esc key
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    run_webcam()
