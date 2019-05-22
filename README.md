# gif2text
A tool for generating text animations from animated GIFs

<p float="left">
  <img src="https://media.giphy.com/media/S7KCMwSDbYp0aZmJVf/giphy.gif" height="210" />
  <img src="https://media.giphy.com/media/h8ySH84tMHuUKg0ORX/giphy.gif" height="210" />
  <img src="https://media.giphy.com/media/Uq44xvgxtvtsNoejSQ/giphy.gif" height="210" />
</p>
<p float="left">
  <img src="https://media.giphy.com/media/l5JI56dZ1UhnehgmdE/giphy.gif" height="370" />
  <img src="https://media.giphy.com/media/JohGkJxRiXkgq11Cl7/giphy.gif" height="370" />
</p>

## Features
1. Support customization of the text layout and appearance, including the number of rows and columns, the text font and size.
2. Support both colored and grayscale text.
3. Support multiple languages, such as English (ASCII) and Chinese.
4. Users can specify their own set of characters to be shown, instead of randomly sampled characters from ASCII or Chinese characters.

## Requirements
The packages required are numpy, pillow, tqdm, imageio.
You can install them all using `pip install numpy pillow tqdm imageio`.

## Usage
The simplest usage is to run the following command
```
python gif2text.py --gif_path=path/to/your/file.gif --out_path=path/to/your/output.gif
```
where you should replace `path/to/your/file.gif` and `path/to/your/output.gif` with your own paths. This command will generate a text animated GIF with default settings, such as using ASCII characters and max number of columns or rows set to 30 (See the right of the top row of the examples above).

You can use the following command to see a list of all possible options to control the appearance of the text animations such as fonts and character set:
```
python gif2text.py --help
```

For example, you can generate texts with Chinese characters and grayscale (black and white) style:
```
python gif2text.py --gif_path=path/to/your/file.gif --out_path=path/to/your/output.gif --charset=chinese --grayscale=True --equalization=True
```
Note that we used `--equalization=True` to increase the contrast of the resulting GIFs.

## Note
1. If you want to use characters other than ASCII or Chinese, you can just put all the characters into a `.txt` file, and use the `--charset=path/to/your/charset/file.txt` option to specify. You can also use such a `.txt` file to specify a subset of ASCII or Chinese characters, or a mix of them, to be used.
2. If you use `--grayscale=True`, it is recommended to use `--equalization=True` to increase the constrast. Otherwise, the pattern in the text animations may be hard to distinguish.
3. Sometimes you may want to use `--denoise=True` to reduce the noise due to downsampling. But this will potentially get rid of some important fine details, so it is set to `False` by default.
4. You can use `--reverse_color` to reverse the colors (or intensities for grayscale) before conversion. This may help if you want to make a dark part white or a bright part dark.
5. I do not do any optimization to compress the file size of the output GIF, so it may be a bit large for Internet transfer. You can you use other tools such as `ImageMagick` to reduce the file size.
