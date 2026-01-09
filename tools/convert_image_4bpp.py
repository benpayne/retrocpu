#!/usr/bin/env python3
"""
Convert an image to 4BPP format for RetroCPU GPU

Output format:
- .raw file: Packed 4BPP pixel data (2 pixels per byte)
- .pal file: Palette data (16 entries, 3 bytes each: R, G, B in 4-bit format)

Author: RetroCPU Project
License: MIT
"""

from PIL import Image
import sys
import argparse


def convert_12bpp(img):
    """Decimate 8-bit RGB to 4-bit RGB (12bpp total)"""
    out_img = img.copy()
    pixels = []
    for px in out_img.getdata():
        # Keep only upper 4 bits of each color channel
        pixels.append((px[0] & 0xF0, px[1] & 0xF0, px[2] & 0xF0))
    out_img.putdata(pixels)
    return out_img


def convert_image(image_file, out_file, num_colors, image_width, image_height):
    """Convert image to 4BPP format with adaptive palette"""

    # Load and resize image
    im = Image.open(image_file)
    sm_img = im.resize((image_width, image_height)).convert("RGB")

    # Decimate to 12bpp (4 bits per channel) before palette conversion
    # This ensures palette matches hardware capabilities
    sm_img_12bpp = convert_12bpp(sm_img)

    # Convert to palette mode with adaptive quantization
    # Use older PIL API compatible with version 9.0.1
    sm_img_clut = sm_img_12bpp.quantize(colors=num_colors, method=2)  # 2 = MEDIANCUT

    # Write pixel data
    with open(f"{out_file}.raw", "wb") as f:
        if num_colors == 16:
            # Pack 2 pixels per byte (4 bits each)
            pixels = list(sm_img_clut.getdata())
            for i in range(0, len(pixels), 2):
                # Upper nibble = first pixel, lower nibble = second pixel
                byte_val = ((pixels[i] & 0x0F) << 4) | (pixels[i+1] & 0x0F if i+1 < len(pixels) else 0)
                f.write(bytes([byte_val]))
        else:
            # 8BPP mode (not used for retrocpu, but keep for reference)
            for px in sm_img_clut.getdata():
                f.write(bytes([px]))

    # Extract palette
    palette_data = sm_img_clut.getpalette()

    # Write palette data (R, G, B for each color)
    with open(f"{out_file}.pal", "wb") as f:
        for i in range(num_colors):
            r = palette_data[i * 3 + 0]
            g = palette_data[i * 3 + 1]
            b = palette_data[i * 3 + 2]

            # Convert to 4-bit per channel (match GPU hardware)
            r4 = r >> 4
            g4 = g >> 4
            b4 = b >> 4

            # Write as 3 separate bytes (R, G, B)
            f.write(bytes([r4, g4, b4]))

            print(f"Palette {i:2d}: RGB({r4:X}, {g4:X}, {b4:X})")

    print(f"\nConverted {image_file} to {image_width}x{image_height} with {num_colors} colors")
    print(f"Output files: {out_file}.raw ({image_width * image_height // 2} bytes), {out_file}.pal ({num_colors * 3} bytes)")


def main():
    parser = argparse.ArgumentParser(description="Convert image to 4BPP format for RetroCPU")
    parser.add_argument("imagefile", help="Input image file")
    parser.add_argument("outfile", help="Output file prefix (without extension)")
    parser.add_argument("-c", "--numcolors", help="Number of colors in palette", type=int, default=16)
    parser.add_argument("-x", "--width", help="Output width in pixels", type=int, default=160)
    parser.add_argument("-y", "--height", help="Output height in pixels", type=int, default=100)
    args = parser.parse_args()

    if args.numcolors != 16:
        print(f"Warning: RetroCPU 4BPP mode only supports 16 colors. Using 16.")
        args.numcolors = 16

    convert_image(args.imagefile, args.outfile, args.numcolors, args.width, args.height)


if __name__ == "__main__":
    main()
