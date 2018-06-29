from distutils.core import setup
import display_manager

setup(
    name='Display Manager',
    version=display_manager.attributes['version'],
    url='https://github.com/univ-of-utah-marriott-library-apple/display_manager',
    author='Adam Davies, Marriott Library IT Services',
    author_email='mlib-its-mac-github@lists.utah.edu',
    description=('A command-line utility to manipulate your Mac\'s display settings.'),
    license='MIT',
    scripts=['display_manager.py'],
    classifiers=[
        'Development Status :: 5 - Stable',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7'
    ],
)
