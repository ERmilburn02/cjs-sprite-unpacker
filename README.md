# Card-Jitsu Snow Sprite Unpacker

Unpacks the sprites from Card-Jitsu Snow's TPK files.

## Requirements

- Python 3
  - Pillow
  - termcolor
- ImageMagick

## Usage

```
unpacker.py [-h] [--output OUTPUT] [--keep-jxr] [--extract-frames] [--create-gif] input

-h, --help            show this help message and exit
--output OUTPUT       Specify output directory (defaults to 'output')
--keep-jxr            Do not delete intermediate JXR files
--extract-frames      Extract individual frames from animations
--create-gif          Create animated GIFs from extracted frames (requires ImageMagick)
input                 Path to the TPK file to unpack
```

## License

Code is under the MIT license
The included JXRDecApp binary is under the BSD 2-Clause License

## Help?
no
