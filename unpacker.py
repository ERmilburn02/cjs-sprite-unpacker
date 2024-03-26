#!/usr/bin/env python3

from tpk.tpk.decoder import TPKDecoder
from PIL import Image, ImageOps

import os
import json
import subprocess
import sys
import argparse
import tempfile
import glob

def path_to_filename_without_extension(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]

def convert_jxr_to_png(jxr_path: str, png_path: str) -> None:
    """
    Convert a JXR image to PNG format.

    Args:
        jxr_path (str): The path to the JXR image file.
        png_path (str): The path to save the converted PNG image.

    Returns:
        None
    """

    # ImageMagick can't convert directly, so we use JXRDecApp to convert
    # to TIFF, and then from there to PNG
    # oh, and Pillow also can't handle JXR

    print("Converting " + jxr_path + " to " + png_path)

    # temp path for tiff file
    tempdir = tempfile.TemporaryDirectory()
    tiff_path = tempdir.name + "/" + path_to_filename_without_extension(jxr_path) + ".tif"

    subprocess.run([".native/JXRDecApp", "-i", jxr_path, "-o", tiff_path])
    subprocess.run(["magick", "convert", tiff_path, png_path])
    os.remove(tiff_path)
    tempdir.cleanup()

    print("Converted " + jxr_path + " to " + png_path)

def unpack_tpk(path: str, output_dir: str, keep_jxr: bool = False) -> None:
    """
    Unpacks a TPK file located at `path` and saves the extracted contents to the `output_dir` directory.
    
    Args:
        path (str): The path to the TPK file.
        output_dir (str): The directory where the extracted contents will be saved.
        keep_jxr (bool, optional): Whether to keep the JXR file after converting it to PNG. Defaults to False.
    
    Returns:
        None
    """
    print("Unpacking " + path)
    decoder = TPKDecoder.from_file(path)
    filename = path_to_filename_without_extension(path)

    decoder.export_json(output_dir + "/" + filename + ".json")
    decoder.export_atlas(output_dir + "/" + filename + ".jxr")

    convert_jxr_to_png(output_dir + "/" + filename + ".jxr", output_dir + "/" + filename + ".png")

    if not keep_jxr:
        os.remove(output_dir + "/" + filename + ".jxr")

    with open(output_dir + "/" + filename + ".scale" + ".json", 'w') as file:
        json.dump(decoder.scale, file, indent=4)

    with open(output_dir + "/" + filename + ".interval" + ".txt", 'w') as file:
        file.write(str(decoder.interval))

    print("Unpacked " + path)

def extract_frames(json_file: str, png_file: str, output_dir: str) -> None:
    """
    Extracts frames from a sprite sheet and saves them as individual images.

    Args:
        json_file (str): The path to the JSON file containing frame data.
        png_file (str): The path to the PNG file containing the sprite sheet.
        output_dir (str): The directory where the individual frames will be saved.

    Returns:
        None
    """
    with open(json_file, 'r') as f:
        data = json.load(f)
        sprite_sheet = Image.open(png_file)

        for frame_data in data["frames"]:
            filename = frame_data['filename']
            frame_info = frame_data['frame']
            sprite_source_size = frame_data['spriteSourceSize']
            source_size = frame_data['sourceSize']
            trimmed = frame_data.get('trimmed', False)  # Check if the frame is trimmed
            rotated = frame_data.get('rotated', False)  # Check if the frame is rotated
            x, y, w, h = frame_info['x'], frame_info['y'], frame_info['w'], frame_info['h']

            spriteSourceSizeX = sprite_source_size['x']
            spriteSourceSizeY = sprite_source_size['y']
            spriteSourceSizeW = sprite_source_size['w']
            spriteSourceSizeH = sprite_source_size['h']
            sourceWidth = source_size['w']
            sourceHeight = source_size['h']

            # Crop frame from sprite sheet
            if rotated:
                frame = sprite_sheet.crop((x, y, x+h, y+w))  # Swap width and height for rotated frame
                frame = frame.transpose(method=Image.ROTATE_90)  # Transpose for rotation by 90 degrees
            else:
                frame = sprite_sheet.crop((x, y, x+w, y+h))
            
            # Calculate borders based on source and sprite source size
            left_border = spriteSourceSizeX
            upper_border = spriteSourceSizeY
            right_border = sourceWidth - spriteSourceSizeW - left_border
            lower_border = sourceHeight - spriteSourceSizeH - upper_border
            
            # Add transparent borders to the image
            frame = ImageOps.expand(frame, (left_border, upper_border, right_border, lower_border), fill=(0, 0, 0, 0))

            # Save individual frame
            frame.save(output_dir + "/" + filename)

def create_gif(input_dir: str, source_name: str, output_file: str, interval: int) -> None:
    """
    Creates a GIF file from a set of PNG images using the ImageMagick command line tool.

    Args:
        input_dir (str): The directory containing the PNG images.
        source_name (str): The name of the source file.
        output_file (str): The path and name of the output GIF file.
        interval (int): The delay between frames in the GIF, in tenths of a second.

    Returns:
        None
    """
    # HACK: Really didn't want to use magick here, but it's the only way I could get it to work
    subprocess.run(["magick", "-delay", str(interval / 10), "-loop", "0", "-dispose", "2", input_dir + "/[a-z_]*_[0-9][0-9][0-9][0-9].png", "-coalesce", output_file])
    pass

def main():
    """
    Unpacks TPK files and performs various operations on the extracted files.

    This function parses command line arguments using the argparse module to specify the input file, output directory,
    options to keep JXR files, extract frames, and create GIFs. It then checks if the output directory exists and creates
    it if necessary. The function calls the unpack_tpk function to unpack the TPK file, passing the input file path,
    output directory, and the keep JXR option. If the extract frames option is specified, the function calls the
    extract_frames function, passing the JSON file path, PNG file path, and output directory. If the create GIF option
    is specified, the function reads the interval value from a file, converts it to an integer, and calls the create_gif
    function, passing the output directory, GIF file name, PNG file path, and interval.

    Parameters:
        None

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description="Unpack TPK files")
    parser.add_argument("input", type=str, help="Input file")
    parser.add_argument("--output", "-o", type=str, help="Output directory", required=False, default="output")
    parser.add_argument("--keep-jxr", "-k", action="store_true", help="Keep JXR files", required=False)
    parser.add_argument("--extract-frames", "-e", action="store_true", help="Extract frames", required=False)
    parser.add_argument("--create-gif", "-g", action="store_true", help="Create GIF", required=False)
    args = parser.parse_args()

    print("Input file:", args.input)
    print("Output directory:", args.output)
    print("Keep JXR files:", args.keep_jxr)

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    unpack_tpk(args.input, args.output, args.keep_jxr)

    if args.extract_frames:
        extract_frames(args.output + "/" + path_to_filename_without_extension(args.input) + ".json", args.output + "/" + path_to_filename_without_extension(args.input) + ".png", args.output)

        if args.create_gif:
            with open(args.output + "/" + path_to_filename_without_extension(args.input) + ".interval" + ".txt", 'r') as file:
                intervalAsString = file.read()

                interval = int(intervalAsString)

                create_gif(args.output, path_to_filename_without_extension(args.input) ,args.output + "/" + path_to_filename_without_extension(args.input) + ".gif", interval)

if __name__ == "__main__":
    main()