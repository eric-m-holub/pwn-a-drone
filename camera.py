import cv2

def display_rtsp_stream(rtsp_url):
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print("Error: Could not open RTSP stream.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to get frame from stream.")
            break

        cv2.imshow('Drone Stream', frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    rtsp_url = "rtsp://192.168.1.1:7070/webcam"  # Change this to your stream URL
    display_rtsp_stream(rtsp_url)
