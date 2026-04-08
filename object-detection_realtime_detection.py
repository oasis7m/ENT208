"""
实时物体识别 - Python版本
使用 OpenCV + YOLOv8
"""

import cv2
from ultralytics import YOLO

# 加载预训练模型（首次运行会自动下载）
model = YOLO('yolov8n.pt')  # n是轻量版，还有s/m/l/x可选

# 打开摄像头
cap = cv2.VideoCapture(0)  # 0是默认摄像头

if not cap.isOpened():
    print("无法打开摄像头")
    exit()

print("按 'q' 键退出")

while True:
    ret, frame = cap.read()
    if not ret:
        print("无法获取画面")
        break

    # 实时检测
    results = model(frame, verbose=False)

    # 绘制检测结果
    for result in results:
        for box in result.boxes:
            # 获取坐标、类别、置信度
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            label = model.names[cls]

            # 绘制边界框
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 绘制标签
            text = f"{label} {conf:.2f}"
            cv2.putText(frame, text, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # 显示画面
    cv2.imshow('Real-time Object Detection', frame)

    # 按q退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放资源
cap.release()
cv2.destroyAllWindows()
