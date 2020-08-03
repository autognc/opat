# Object Pose Annotation Tool

**UPDATE**: This project is archived. See https://github.com/autognc/opat-js for the updated, web-based tool.

A lightweight interactive 6D pose annotation tool. Loads images from a directory and overlays a 3D model on top of them, allowing
the user to line up the model and an object in the image using keyboard shortcuts. Requires camera intrinsics to be known.

## Requirements
- [SciPy](https://www.scipy.org/) for manipulating rotations
- [trimesh](https://github.com/mikedh/trimesh) for loading the 3D model
- [pyrender](https://github.com/mmatl/pyrender) for rendering the 3D model
- [pyglet](http://pyglet.org/) for the display window

## Usage

```
$ git clone https://github.com/autognc/opat
$ cd opat
$ pip install -e .
$ opat --help
usage: opat [-h] directory model_path output_path

positional arguments:
  directory    Path to image directory (as well as intrinsics file).
  model_path   Path to 3D model, any filetype supported by trimesh.
  output_path  Output path for poses, JSON. Will load poses if path exists
               already.

optional arguments:
  -h, --help   show this help message and exit
$ opat my-images my-model.stl poses.json
```

The image directory must contain a file called `intrinsics.json`, with the format:
```
{
  "image_file_name": [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]
}
```
The file must have an entry for every image in the image directory.

## Keyboard Shortcuts
See [opat/config.py](opat/config.py) for keybindings. The pose information is saved upon every `next_image` and `previous_image` action.
