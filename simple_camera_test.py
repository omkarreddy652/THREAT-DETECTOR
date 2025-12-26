#!/usr/bin/env python3
"""
Simple camera test - shows what the camera is capturing
"""

import os
import sys

try:
    import cv2
except Exception:
    print("OpenCV (cv2) is required for this script. Install with: pip install opencv-python")
    sys.exit(1)

def main():
    print("Opening camera...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Cannot open camera")
        return 1

    print("✅ Camera opened")
    print("Camera is capturing frames...")
    print("Press 'q' to quit, 's' to save screenshot")

    frame_count = 0
    screenshots_dir = os.path.join(os.getcwd(), "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame")
                break

            frame_count += 1

            # Show resolution
            height, width = frame.shape[:2]
            text = f"Frame {frame_count} - {width}x{height}"
            cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Add crosshair
            center_x, center_y = width // 2, height // 2
            cv2.line(frame, (center_x - 50, center_y), (center_x + 50, center_y), (0, 0, 255), 2)
            cv2.line(frame, (center_x, center_y - 50), (center_x, center_y + 50), (0, 0, 255), 2)

            cv2.imshow("Camera Feed - Press 'q' to quit", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = os.path.join(screenshots_dir, f"screenshot_{frame_count}.jpg")
                try:
                    cv2.imwrite(filename, frame)
                    print(f"✅ Screenshot saved: {filename}")
                except Exception as e:
                    print(f"Failed to save screenshot: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()

    print(f"Total frames captured: {frame_count}")
    print("Done!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
