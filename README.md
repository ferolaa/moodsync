# Gesture-Controlled Drawing Studio

**A real-time computer vision application for drawing and interacting with a digital canvas using hand gestures.**

## Overview

This project explores touchless human-computer interaction through webcam-based hand tracking. Using MediaPipe and OpenCV, the application detects hand landmarks and interprets gestures to control a digital drawing interface.

The repository contains several iterations, progressing from a basic hand-drawing application to a more advanced interactive studio.

## Key Features

- Real-time hand detection and landmark tracking
- Drawing, erasing and canvas clearing using hand gestures
- Interactive color palette and adjustable brush settings
- Graphical interface with drawing and selection controls
- Stroke selection and deletion
- Stroke smoothing and optional straightening
- Exporting drawings as PNG and SVG
- Optional image-to-3D conversion through the third-party Meshy API

## Technologies

| Technology | Purpose |
| --- | --- |
| Python | Core application logic |
| MediaPipe | Hand landmark detection |
| OpenCV | Webcam processing and graphical interface |
| NumPy | Image and canvas operations |
| Requests | Optional external API communication |
| python-dotenv | Local API key configuration |

## Project Files

- hand_drawing_app.py — Initial gesture-controlled drawing application
- 3rd_version.py — Expanded interface with drawing tools and color selection
- GUI_hand_drawing.py — Advanced implementation with stroke editing, export and optional 3D integration
- drawing.png — Example drawing output

## Getting Started

Install the required Python libraries:

```bash
python -m pip install opencv-python mediapipe numpy requests python-dotenv
```

Run the advanced version:

```bash
python GUI_hand_drawing.py
```

A functioning webcam and camera permissions are required.

## Keyboard Shortcuts

| Key | Action |
| --- | --- |
| Q | Quit |
| M | Toggle selection mode |
| X | Delete selected stroke |
| S | Save PNG |
| V | Save SVG |
| T | Toggle stroke straightening |
| C | Clear the canvas |
| 3 | Trigger optional image-to-3D conversion |

The image-to-3D feature requires a separately configured MESHY_API_KEY in a local .env file. It sends an image of the canvas to the external Meshy service and may incur usage costs. Never commit the API key.

## Skills Demonstrated

Computer Vision, Real-Time Image Processing, Hand Tracking, Gesture Recognition, Human-Computer Interaction, Python Application Development and API Integration.

## Limitations

This is a research and demonstration application. Webcam lighting, hand visibility and hardware performance may affect gesture detection. The optional 3D feature relies on an external service rather than a locally trained model.

## Credits

Collaborative Computer Vision project. Individual contributors and their roles should be credited before public release.
