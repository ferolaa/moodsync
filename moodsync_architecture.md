# MoodSync Architecture

Here is the system architecture specific to the MoodSync project, reflecting how the components interact in your codebase:

```mermaid
graph LR
    Webcam[Webcam]:::gray --> Camera[Camera Module]:::purple
    Camera -- frames --> Emotion[Emotion Thread]:::orange
    Camera -- frames --> Gestures[Gestures Thread]:::green
    
    Emotion -- mood --> State[Shared State]:::blue
    Gestures -- "gestures, volume" --> State
    
    State -- state snapshot --> Main[Main Loop]:::yellow
    
    Main -- current mood --> Fusion[Fusion Layer]:::pink
    Fusion -- target playlist --> Main
    
    Main -- music control --> Audio[Audio Player]:::gray
    Main -- UI render --> Display[Display Dashboard]:::gray

    classDef gray fill:#c4c4c4,stroke:#333,stroke-width:1px,color:#000,rx:5px,ry:5px;
    classDef purple fill:#e6b8ff,stroke:#333,stroke-width:1px,color:#000,rx:5px,ry:5px;
    classDef orange fill:#ffb854,stroke:#333,stroke-width:1px,color:#000,rx:5px,ry:5px;
    classDef green fill:#8ce058,stroke:#333,stroke-width:1px,color:#000,rx:5px,ry:5px;
    classDef blue fill:#5271ff,stroke:#333,stroke-width:1px,color:#000,rx:5px,ry:5px;
    classDef yellow fill:#ffda5c,stroke:#333,stroke-width:1px,color:#000,rx:5px,ry:5px;
    classDef pink fill:#ff99cc,stroke:#333,stroke-width:1px,color:#000,rx:5px,ry:5px;
```

### Flow Breakdown:
1. **Camera Module (`camera.py`)**: Runs continuously to grab frames from the webcam and avoids multiple processes fighting for access.
2. **Input Threads (`inputs/emotion.py` & `inputs/gestures.py`)**: Analyze frames in the background using MediaPipe to extract mood and gestures (e.g. swipes, volume levels).
3. **Shared State (`state.py`)**: Acts as a thread-safe data store. The input threads write predictions here, preventing blocking.
4. **Main Loop (`main.py`)**: Reads a snapshot of the shared state every frame.
5. **Fusion Layer (`fusion.py`)**: A logic mapper that tells the Main Loop which playlist corresponds to the current mood.
6. **Output (Pygame)**: The Main Loop handles UI rendering (video, dashboard) and executes audio commands (play, pause, switch playlists).
