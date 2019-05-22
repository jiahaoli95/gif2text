import argparse
import os
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageOps, ImageFilter
from tqdm import tqdm
import imageio


def get_ascii_chars():
    return ''.join(chr(x) for x in range(32, 127))


def get_chinese_chars():
    return open('assets/cn_charset.txt').read().strip() + ' '


def is_ascii(s):
    try:
        s.encode('ascii')
    except UnicodeEncodeError:
        return False
    else:
        return True


def read_gif(path):
    im_list = imageio.mimread(path)
    im_list = [im[:, :, :3] for im in im_list]
    for i in range(1, len(im_list)):
        im_list[i] = np.where(im_list[i]>0, im_list[i], im_list[i-1])
    duration = Image.open(path).info['duration'] / 1000.
    return im_list, duration


class Font():
    def __init__(self, path, size):
        self.font = ImageFont.truetype(font=path, size=size)
        width, height = self.font.getsize('A')
        self.patch_size = max(width, height)
        self.x_offset = (self.patch_size-width)//2
        self.y_offset = (self.patch_size-height)//2


    def get_patches(self, chars):
        size = self.patch_size
        patches = np.zeros([len(chars), size, size], dtype=np.uint8)
        if len(set(chars)) != len(chars):
            raise Exception('Duplicate characters exist')
        for i, c in enumerate(chars):
            p = np.zeros([size, size], dtype=np.uint8)
            p = Image.fromarray(p)
            draw = ImageDraw.Draw(p)
            draw.text([self.x_offset, self.y_offset], c, fill='white', font=self.font)
            patches[i] = p
        return patches


def get_rank(arr):
    temp = np.argsort(arr)
    ranks = np.empty_like(temp)
    ranks[temp] = np.arange(len(arr))
    return ranks


# get intensities for patches
def get_intensities(patches):
    densities = np.mean(patches, (1, 2)) / 255.
    intensities = get_rank(densities)
    scale = 255./np.max(intensities)
    intensities = intensities.astype(np.float32)
    intensities *= scale
    intensities = intensities.astype(np.uint8)
    return intensities


# get a 256-element numpy array containing the index of characters
def get_intensity2idx(chars, intensities):
    d = {}
    for idx, intensity in zip(range(len(chars)), intensities):
        if intensity in d:
            d[intensity].append(idx)
        else:
            d[intensity] = [idx]
    unique_intensities = []
    char_idx = []
    for intensity in d:
        unique_intensities.append(intensity)
        char_idx.append(np.random.choice(d[intensity]))
    unique_intensities = np.array(unique_intensities, dtype=np.uint8)
    char_idx = np.array(char_idx, dtype=np.int64)
    intensity2idx = np.arange(256, dtype=np.int64)
    intensity2idx = intensity2idx[:, np.newaxis] - unique_intensities[np.newaxis, :]
    intensity2idx = np.abs(intensity2idx)
    intensity2idx = np.argmin(intensity2idx, -1)
    intensity2idx = char_idx[intensity2idx]
    return intensity2idx


# convert one frame to text image
def im2text(im, patches, intensity2idx, grayscale=False):
    im = np.array(im, dtype=np.uint8)
    patch_size = patches.shape[-1]
    im_h, im_w, im_c = im.shape
    text_im_w = im_w * patch_size
    text_im_h = im_h * patch_size
    gray_im = Image.fromarray(im.copy())
    gray_im = np.array(gray_im.convert('L'))
    idx = intensity2idx[gray_im]
    text_im = patches[idx]
    if grayscale:
        text_im = text_im.transpose([0, 2, 1, 3])
        text_im = text_im.reshape([text_im_h, text_im_w])
    else:
        text_im = text_im[..., np.newaxis].astype(np.float32)
        im = im[:, :, np.newaxis, np.newaxis, :].astype(np.float32)
        text_im = text_im * im / 255.
        text_im = text_im.astype(np.uint8)
        text_im = text_im.transpose([0, 2, 1, 3, 4])
        text_im = text_im.reshape([text_im_h, text_im_w, im_c])
    return text_im


# convert a list of frames to text image
def images2text(im_list, chars, font, grayscale=False):
    chars = ''.join(list(set(chars)))
    patches = font.get_patches(chars)
    intensities = get_intensities(patches)
    intensity2idx = get_intensity2idx(chars, intensities)
    text_images = []
    print('Converting GIF to text animations...')
    for im in tqdm(im_list):
        text_images.append(im2text(im, patches, intensity2idx, grayscale=grayscale))
    print('Conversion done.')
    return text_images


if __name__ == '__main__':
    # parse arguments
    arg_bool = lambda x: x.lower() in ['true', 't', '1']
    parser = argparse.ArgumentParser()
    parser.add_argument('--gif_path', type=str, help='Path to the GIF file.')
    parser.add_argument('--out_path', type=str, help='Path of the output gif file (including the filename).')
    parser.add_argument('--width', type=int, help='Number of characters per row. You can specify only width or height. The other will be automatically set to maintain the aspect ratio.', default=None)
    parser.add_argument('--height', type=int, help='Number of characters per column. You can specify only width or height. The other will be automatically set to maintain the aspect ratio.', default=None)
    parser.add_argument('--charset', type=str, help='"ascii", "chinese", or a path to a .txt file containing all the characters to be shown.', default='ascii')
    parser.add_argument('--font', type=str, help='Path to a .ttf or .ttc font file you want to use.', default=None)
    parser.add_argument('--font_size', type=int, help='Font size. Default is 15.', default=15)
    parser.add_argument('--reverse_color', type=arg_bool, help='Reverse colors (black to white and white to black) before generating text animations.', default='False')
    parser.add_argument('--equalization', type=arg_bool, help='Perform histogram equalization. It helps when the constrast of the original GIF is low, especially when grayscale=True. If grayscale=False, this should not be used since the colors may be changed drastically.', default='False')
    parser.add_argument('--denoise', type=arg_bool, help='Perform denoising before converting to text. Sometimes it may help to reduce noise due to downsampling, but some fine details may be lost', default='False')
    parser.add_argument('--grayscale', type=arg_bool, help='Output grayscale text GIF. If you set it to True, almost always you also want to set equalization=True.', default='False')
    opts = parser.parse_args()

    # check path
    if not os.path.exists(opts.gif_path):
        raise Exception('GIF file not exists.')
    # read gif
    im_list, duration = read_gif(opts.gif_path)
    # set width and height
    im_height, im_width, _ = im_list[0].shape
    cond1 = opts.width is None
    cond2 = opts.height is None
    if cond1 and cond2:
        scale = 30. / max(im_width, im_height)
        width = im_width * scale
        height = im_height * scale
    elif cond1 and not cond2:
        height = opts.height
        width = float(height) / im_height * im_width
    elif not cond1 and cond2:
        width = opts.width
        height = float(width) / im_width * im_height
    else:
        width = opts.width
        height = opts.height
    width = int(width)
    height = int(height)
    for i, im in enumerate(im_list):
        im = Image.fromarray(im)
        im = im.resize([width, height])
        im = np.array(im)
        im_list[i] = im
    # reverse intensities
    if opts.reverse_color:
        im_list = [255-im for im in im_list]
    # denoise
    if opts.denoise:
        median_filter = ImageFilter.MedianFilter()
        for i, im in enumerate(im_list):
            im = Image.fromarray(im)
            im = im.filter(median_filter)
            im = np.array(im, dtype=np.uint8)
            im_list[i] = im
    # histogram equalization
    if opts.equalization:
        for i, im in enumerate(im_list):
            for channel in range(im.shape[-1]):
                equalized = ImageOps.equalize(Image.fromarray(im[:, :, channel]))
                im[:, :, channel] = equalized
            im = np.array(im, dtype=np.uint8)
            im_list[i] = im
    # set charset
    opts.charset = opts.charset.lower()
    if opts.charset == 'ascii':
        chars = get_ascii_chars()
    elif opts.charset == 'chinese':
        chars = get_chinese_chars()
    else:
        chars = open(opts.charset).read().strip()
    # set font
    if opts.font is None:
        if opts.charset == 'ascii':
            font_path = 'assets/Inconsolata-Bold.ttf'
        elif opts.charset == 'chinese':
            font_path = 'assets/SourceHanSans-Bold.ttc'
        elif is_ascii(chars):
            font_path = 'assets/Inconsolata-Bold.ttf'
        else:
            font_path = 'assets/SourceHanSans-Bold.ttc'
    else:
        font_path = opts.font
    font = Font(font_path, opts.font_size)
    # convert
    text_images = images2text(im_list, chars, font, grayscale=opts.grayscale)
    print('Writing to %s' % opts.out_path)
    imageio.mimwrite(opts.out_path, text_images, duration=duration)
    print('All Done!')
