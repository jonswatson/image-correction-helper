# Image Correction Helper

A PyQt6-based application for correcting perspective distortion in images, particularly useful for grid-based images.

## Features

- Load and display images
- Select four corner points to define the grid area
- Adjust grid size (rows and columns)
- Preview perspective correction in real-time
- Save corrected images
- Pan and zoom functionality

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/image-correction-helper.git
cd image-correction-helper
```

2. Create and activate a conda environment:
```bash
conda env create -f environment.yml
conda activate grid-correction
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. **Launch the Application**
```bash
python run.py
```

2. **Load an Image**
   - Click "Load Image" in the toolbar
   - Select an image file (supported formats: PNG, JPG, JPEG, BMP, GIF)

3. **Select Grid Points**
   - Click on the image to place four corner points
   - Points can be dragged to adjust their position
   - Right-click a point to remove it
   - Points must be placed in any order - the application will automatically determine the correct orientation

4. **Adjust Grid Size**
   - Use the row and column spinboxes in the toolbar to set the desired grid size
   - The grid will update automatically

5. **Preview Correction**
   - Check the "Preview Perspective" checkbox to see the corrected image
   - The grid will turn semi-transparent green
   - Points will be hidden during preview
   - Use space bar + drag to pan the preview
   - Uncheck to return to the original view

6. **Save the Result**
   - Click "Save Image" in the toolbar
   - Choose a location and filename for the corrected image

## Tips

- The application automatically orders the points to minimize rotation and flipping
- You can adjust points at any time before saving
- The preview shows how the grid will look when corrected
- Pan and zoom are always available, even during preview
- Grid adjustments are only possible in the original view

## Requirements

- Python 3.10+
- PyQt6
- OpenCV
- NumPy

## License

[Your chosen license]

## Contributing

[Your contribution guidelines] 