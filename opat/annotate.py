import numpy as np
import pyglet
import trimesh
import pyrender
import argparse
from scipy.spatial.transform import Rotation
from . import config
import os
from PIL import Image
import glob
import json


class ModelRenderer:
    def __init__(self, model_path):
        mesh = pyrender.Mesh.from_trimesh(trimesh.load(model_path))
        self.scene = pyrender.Scene(ambient_light=[0.5, 0.5, 0.5, 1.0], bg_color=(0, 0, 0))
        self.object_node = pyrender.Node(mesh=mesh)
        self.scene.add_node(self.object_node)

    def render(self, width, height, intrinsics, rotation, translation):
        camera = pyrender.IntrinsicsCamera(intrinsics[0][0], intrinsics[1][1], intrinsics[0][2], intrinsics[1][2], zfar=1000)
        camera_node = pyrender.Node(camera=camera, rotation=Rotation.from_euler('x', 180, degrees=True).as_quat())
        self.scene.add_node(camera_node)

        self.object_node.translation = translation
        self.object_node.rotation = rotation.as_quat()

        image, depth = pyrender.OffscreenRenderer(
            viewport_height=height, viewport_width=width, point_size=1.0
        ).render(self.scene, flags=pyrender.RenderFlags.ALL_WIREFRAME)
        self.scene.remove_node(camera_node)
        return image


class PoseAnnotator:
    def __init__(self, model_path, image_directory, output_path):
        self.output_path = output_path
        self.image_paths = self.load_image_paths(image_directory)
        self.intrinsics = self.load_intrinsics(image_directory)
        self.poses = self.load_poses(output_path)

        if self.intrinsics.keys() != set(os.path.basename(path) for path in self.image_paths):
            raise ValueError('Intrinsics keys and image filenames do not match.')

        if set(self.poses.keys()).difference(set(os.path.basename(path) for path in self.image_paths)):
            raise ValueError('Found existing output file with keys that do not match image filenames.')

        self.model_renderer = ModelRenderer(model_path)

        self.window, self.label = self.create_window()
        self.window.on_draw = self.render

        self.current_index = 0
        self.current_image_path = self.current_image = self.current_rotation = self.current_translation = None
        self.load_image()

        self.translation_step = config.TRANSLATION_STEP_BASE
        self.z_step = config.TRANSLATION_Z_BASE
        self.rotation_step = config.ROTATION_STEP_BASE

        self.executing_actions = set()
        self.window.push_handlers(on_key_press=self.handle_keydown, on_key_release=self.handle_keyup)

    @classmethod
    def load_image_paths(cls, path):
        search_paths = [os.path.join(path, f'*.{extension}') for extension in config.IMAGE_FILE_EXTENSIONS]
        globs = [glob.glob(path) for path in search_paths]
        image_paths = sum(globs, [])
        if not image_paths:
            raise ValueError('No images found.')
        return sorted(image_paths)

    @classmethod
    def load_intrinsics(cls, path):
        with open(os.path.join(path, config.INTRINSICS_PATH), 'r') as f:
            intrinsics = json.load(f)
        if not isinstance(intrinsics, dict) or not all(
                isinstance(v, list) and np.array(v).shape == (3, 3) for v in intrinsics.values()):
            raise ValueError('Intrinsics file has invalid format.')
        return intrinsics

    @classmethod
    def load_poses(cls, output_path):
        dirname = os.path.dirname(output_path)
        if dirname and not os.path.exists(dirname):
            raise ValueError(f'Could not find path "{dirname}"')
        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                poses = json.load(f)
            if not isinstance(poses, dict) or not all(
                isinstance(v, dict) and
                isinstance(v.get('rotation'), list) and len(v.get('rotation')) == 4 and
                isinstance(v.get('translation'), list) and len(v.get('translation')) == 3
                for v in poses.values()
            ):
                raise ValueError('Found existing output file with invalid format.')
        else:
            poses = {}
        return poses

    @classmethod
    def create_window(cls):
        window = pyglet.window.Window(width=1280, height=720, resizable=True)
        label = pyglet.text.Label(anchor_x='center')
        return window, label

    def load_image(self):
        self.current_image_path = self.image_paths[self.current_index]
        self.current_image = np.array(Image.open(self.current_image_path))[..., :3]
        pose = self.poses.get(os.path.basename(self.current_image_path))
        if pose:
            w, x, y, z = pose['rotation']
            self.current_rotation = Rotation.from_quat([x, y, z, w])
            self.current_translation = pose['translation'].copy()
        elif self.current_translation is None or self.current_rotation is None:
            self.current_rotation = Rotation.identity()
            self.current_translation = config.DEFAULT_TRANSLATION.copy()
        # auto-resize to fit
        # self.window.width = max(self.label.content_width, self.current_image.shape[1])
        # self.window.height = self.label.content_height + self.current_image.shape[0]

    def write_poses(self):
        x, y, z, w = self.current_rotation.as_quat()
        self.poses[os.path.basename(self.current_image_path)] = {
            'rotation': [w, x, y, z],
            'translation': self.current_translation.copy()
        }
        with open(self.output_path, 'w') as f:
            json.dump(self.poses, f)

    def render(self):
        self.window.clear()
        (tx, ty, tz), (rx, ry, rz) = self.current_translation, self.current_rotation.as_euler('xyz', degrees=True)
        self.label.text = (
            f'{self.current_image_path}        '
            f'pos: ({tx:02.2f}, {ty:02.2f}, {tz:02.2f})        '
            f'rot: ({rx:03.2f}, {ry:03.2f}, {rz:03.2f})'
        )
        self.label.anchor_x = 'center'
        self.label.x = self.window.width // 2
        self.label.anchor_y = 'top'
        self.label.y = self.window.height
        self.label.draw()

        height, width = self.current_image.shape[:2]
        model_image = self.model_renderer.render(
            width,
            height,
            self.intrinsics[os.path.basename(self.current_image_path)],
            self.current_rotation,
            self.current_translation,
        )
        self.window.switch_to()
        mask = np.all(model_image == 0, axis=-1, keepdims=True)
        final_image = np.where(
            mask,
            self.current_image,
            (1 - config.OVERLAY_OPACITY) * self.current_image + config.OVERLAY_OPACITY * model_image
        ).astype(np.uint8)
        # image_buffer = (pyglet.gl.GLubyte * final_image.size).from_buffer(final_image)
        image_data = pyglet.image.ImageData(
            width,
            height,
            'RGB',
            final_image.tostring(),
            pitch=-3 * width,
        )
        resize_factor = min(self.window.width / width, self.window.height / height)
        resize_width, resize_height = int(width * resize_factor), int(height * resize_factor)
        image_data.anchor_x = resize_width // 2
        image_data.anchor_y = resize_height
        image_data.blit(
            self.window.width // 2,
            self.window.height - self.label.content_height,
            width=resize_width,
            height=resize_height,
        )

    def do_action(self, action):
        if action in self.executing_actions:
            action()
            pyglet.clock.schedule_once(lambda _: self.do_action(action), config.ACTION_DELAY)

    def handle_keydown(self, symbol, _):
        action_name = config.KEYBINDINGS.get(symbol)
        if not action_name:
            return

        if action_name == 'increase_step_size':
            self.translation_step = config.TRANSLATION_STEP_INCREASED
            self.z_step = config.TRANSLATION_Z_INCREASED
            self.rotation_step = config.ROTATION_STEP_INCREASED
            return
        if action_name == 'decrease_step_size':
            self.translation_step = config.TRANSLATION_STEP_DECREASED
            self.z_step = config.TRANSLATION_Z_DECREASED
            self.rotation_step = config.ROTATION_STEP_DECREASED
            return

        action = getattr(self, action_name, None)
        if not action:
            return
        self.executing_actions.add(action)
        self.do_action(action)

    def handle_keyup(self, symbol, _):
        action_name = config.KEYBINDINGS.get(symbol)
        if not action_name:
            return

        if action_name in ('increase_step_size', 'decrease_step_size'):
            self.translation_step = config.TRANSLATION_STEP_BASE
            self.z_step = config.TRANSLATION_Z_BASE
            self.rotation_step = config.ROTATION_STEP_BASE

        action = getattr(self, action_name, None)
        if not action:
            return
        self.executing_actions.remove(action)

    def next_image(self):
        self.write_poses()
        self.current_index = (self.current_index + 1) % len(self.image_paths)
        self.load_image()

    def previous_image(self):
        self.write_poses()
        self.current_index = (self.current_index - 1) % len(self.image_paths)
        self.load_image()

    def rotate(self, axis, deg):
        self.current_rotation = Rotation.from_rotvec(
            self.current_rotation.apply(np.eye(3)[axis]) * np.radians(deg)
        ) * self.current_rotation

    def translate_up(self):
        self.current_translation[1] -= self.translation_step

    def translate_down(self):
        self.current_translation[1] += self.translation_step

    def translate_left(self):
        self.current_translation[0] -= self.translation_step

    def translate_right(self):
        self.current_translation[0] += self.translation_step

    def translate_backward(self):
        self.current_translation[2] -= self.z_step

    def translate_forward(self):
        self.current_translation[2] += self.z_step

    def rotate_plus_x(self):
        self.rotate(0, self.rotation_step)

    def rotate_minus_x(self):
        self.rotate(0, -self.rotation_step)

    def rotate_plus_y(self):
        self.rotate(1, self.rotation_step)

    def rotate_minus_y(self):
        self.rotate(1, -self.rotation_step)

    def rotate_plus_z(self):
        self.rotate(2, self.rotation_step)

    def rotate_minus_z(self):
        self.rotate(2, -self.rotation_step)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=str, help='Path to image directory (as well as intrinsics file).')
    parser.add_argument('model_path', type=str, help='Path to 3D model, any filetype supported by trimesh.')
    parser.add_argument('output_path', type=str, help='Output path for poses, JSON. Will load poses if path exists already.')
    args = parser.parse_args()

    PoseAnnotator(args.model_path, args.directory, args.output_path)
    pyglet.app.run()


if __name__ == '__main__':
    main()
