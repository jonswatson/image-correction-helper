# Image Correction Helper

A Python application for correcting perspective and distortion in images, particularly useful for grid-based images like graph paper.

## Features

### Phase 1 (Current)
- Basic image viewer with zoom and pan functionality
- Space bar + drag for panning
- Mouse wheel for zooming
- Fit to view option
- Image loading and saving

### Phase 2 (In Progress)
- Point selection system
- Perspective correction
- Grid overlay visualization
- Complex distortion correction

## Requirements

- Python 3.10+
- PyQt6
- OpenCV
- NumPy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/image-correction-helper.git
cd image-correction-helper
```

2. Create and activate a virtual environment:
```bash
conda env create -f environment.yml
conda activate grid-correction
```

3. Run the application:
```bash
python run.py
```

## Usage

1. Load an image using the "Load Image" button
2. Use "Fit to View" to see the entire image
3. Use mouse wheel to zoom in/out
4. Hold space and drag to pan
5. Use "Fit to View" to reset the view

## Development

The project is structured as follows:
```
src/
├── __init__.py
├── main.py
├── gui/
│   ├── __init__.py
│   ├── main_window.py
│   └── image_view.py
└── processing/
    └── __init__.py
```

## License

MIT License 