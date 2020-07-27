from setuptools import setup, find_packages

setup(
    name='opat',
    version='0.1',
    description='Object Pose Annotation Tool',
    license='MIT',
    packages=find_packages(),
    author='Kevin Black',
    install_requires=[
        'pyglet~=1.5',
        'pyrender==0.1.43',
        'numpy',
        'scipy',
        'trimesh',
        'Pillow'
    ],
    entry_points='''
      [console_scripts]
      opat=opat.annotate:main
    ''',
)