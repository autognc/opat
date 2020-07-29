# see https://pyglet.readthedocs.io/en/latest/modules/window_key.html#module-pyglet.window.key for a full list of keys
from pyglet.window import key

KEYBINDINGS = {
    key.W: 'translate_up',
    key.S: 'translate_down',
    key.A: 'translate_left',
    key.D: 'translate_right',
    key.Z: 'translate_forward',
    key.X: 'translate_backward',
    key.LEFT: 'rotate_minus_z',
    key.RIGHT: 'rotate_plus_z',
    key.DOWN: 'rotate_minus_y',
    key.UP: 'rotate_plus_y',
    key.SLASH: 'rotate_minus_x',
    key.PERIOD: 'rotate_plus_x',
    key.LSHIFT: 'decrease_step_size',
    key.LCTRL: 'increase_step_size',
    key.PAGEDOWN: 'next_image',
    key.PAGEUP: 'previous_image',
}

IMAGE_FILE_EXTENSIONS = ['png', 'PNG', 'jpg', 'JPG', 'jpeg', 'JPEG']
INTRINSICS_PATH = 'intrinsics.json'
OVERLAY_OPACITY = 0.9

# meters
TRANSLATION_STEP_BASE = 0.1
TRANSLATION_STEP_INCREASED = 1
TRANSLATION_STEP_DECREASED = 0.01
# step size for translating toward/away from the camera
TRANSLATION_Z_BASE = 1
TRANSLATION_Z_INCREASED = 10
TRANSLATION_Z_DECREASED = 0.1

DEFAULT_TRANSLATION = [0, 0, 30]

# degrees
ROTATION_STEP_BASE = 1
ROTATION_STEP_INCREASED = 10
ROTATION_STEP_DECREASED = 0.1

# seconds
ACTION_DELAY = 50 / 1000
