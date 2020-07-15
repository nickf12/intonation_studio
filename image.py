import json
import math
import random
import os

import cairo
import numpy as np
import shutil

from utils import path_in_medialib, NoteTools, ColorTools


class ImageMaker:
    """
    Create the video frames
    """
    WIDTH, HEIGHT = 1280, 720
    PADDING = 10
    BENCHMARKS = 4
    DRAW_GRID = False
    PATTERN = 'frame_%d.png'

    def __init__(self, data, maker_id=None):
        # Directory Setup
        self.data = data
        self.samples = np.array(self.data['samples'])
        self.id = maker_id if maker_id else random.randint(4, 10)

    def __getattr__(self, name):
        """ Shortcut. The data dictionary is accesible through the object
        """
        if name in self.data:
            return self.data[name]

    def rects(self):
        return {
            'text': (60, 40, 1120, 160),
            'path': (60, 200, 1160, 500),
        }

    @classmethod
    def from_filepath(cls, filepath):
        """
        Create an instance from a file
        """
        out = None
        with open(filepath) as json_file:
            analysis = json.load(json_file)
            out = cls(analysis)
        return out

    def target_path(self, filename):
        return os.path.join(self.targetdir, filename)

    def init_targetdir(self, custom_targetdir=None):
        if custom_targetdir:
            self.targetdir = custom_targetdir
            self.is_custom_targetdir = True
        else:
            self.targetdir = path_in_medialib(f'maker_{self.id}')
            if not os.path.exists(self.targetdir):
                os.makedirs(self.targetdir)

    def remove_targetdir(self):
        if os.path.exists(self.targetdir) and not self.is_custom_targetdir:
            shutil.rmtree(self.targetdir)
            return True
        return False

    def to_image_dim(self, x, dim):
        """
        Map to a space dimension
        """
        scaled_x = None
        if dim == 'path_x':
            # scale time index to the x axis of the path
            scaled_x = self.rects()['path'][2] * \
                (float(x) / float(self.max_x))
        if dim == 'path_y':
            # scale a frequency to the y axis of the path
            scaled_x = self.rects()['path'][3] - self.rects()['path'][3] * \
                (x - self.min_y) / (self.max_y - self.min_y)
        return scaled_x

    def cairo_draw_canvas(self):
        canvas_color = ColorTools.COLOR_3
        surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,
            self.rects()['path'][2] + 2 * self.PADDING,
            self.rects()['path'][3] + 2 * self.PADDING
        )
        ctx = cairo.Context(surface)
        ctx.set_source_rgba(
            *ColorTools.to_rgba_source(canvas_color)
        )
        ctx.rectangle(
            0,
            0,
            self.rects()['path'][2] + 2 * self.PADDING,
            self.rects()['path'][3] + 2 * self.PADDING
        )
        ctx.stroke()
        return surface

    def cairo_draw_grid(self):
        """
        Draw the grid with all the notes.
        Very confusing but useful for debugging
        """
        surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,
            self.rects()['path'][2] + 2 * self.PADDING,
            self.rects()['path'][3] + 2 * self.PADDING
        )
        ctx = cairo.Context(surface)
        ctx.set_source_rgba(
            *ColorTools.to_rgba_source(ColorTools.COLOR_3)
        )

        for note in NoteTools.note_range(self.min_note, self.max_note):
            note_scaled = NoteTools.note_to_midi(note) if \
                self.is_midi else NoteTools.note_to_freq(note)
            y = self.to_image_dim(note_scaled, 'path_y')
            ctx.move_to(0, y + self.PADDING)
            ctx.line_to(self.rects()['path'][2], y + self.PADDING)
        ctx.set_source_rgba(
            **ColorTools.to_rgba_source(ColorTools.COLOR_3)
        )
        ctx.stroke()
        return surface

    def cairo_draw_rects(self):
        """
        Draw semi transparent black rectangles pitch is not defined
        """
        surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,
            self.rects()['path'][2] + 2 * self.PADDING,
            self.rects()['path'][3] + 2 * self.PADDING
        )
        ctx = cairo.Context(surface)
        for x, y in enumerate(self.samples):
            if y == self.no_value or y == 0.0:
                x1 = self.PADDING + self.to_image_dim(x - 0.5, 'path_x')
                x2 = self.PADDING + self.to_image_dim(x + 0.5, 'path_x')
                width = x2 - x1
                ctx.rectangle(
                    x1,
                    0,
                    width,
                    self.rects()['path'][3] + 2 * self.PADDING
                )
                ctx.set_source_rgba(
                    *ColorTools.to_rgba_source(ColorTools.TRANSPARENT_2)
                )
                ctx.fill()
        return surface

    def cairo_draw_circles(self):
        """
        Draw circles only where estamation is relyble
        """
        surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,
            self.rects()['path'][2] + 2 * self.PADDING,
            self.rects()['path'][3] + 2 * self.PADDING
        )
        ctx = cairo.Context(surface)
        for x, y in enumerate(self.samples):
            if y != self.no_value and y != 0.0:
                x1 = self.PADDING + self.to_image_dim(x, 'path_x')
                y1 = self.PADDING + self.to_image_dim(y, 'path_y')
                ctx.arc(x1, y1, 4, 0, 2 * math.pi)
                ctx.set_source_rgba(
                    *ColorTools.to_rgba_source(ColorTools.COLOR_6)
                )
                ctx.fill()
        return surface

    def cairo_draw_benchmarks(self, leaders=5):
        """
        Mark the  most used notes. Very confusing but interesting
        """
        surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,
            self.rects()['path'][2] + 2 * self.PADDING,
            self.rects()['path'][3] + 2 * self.PADDING
        )
        ctx = cairo.Context(surface)
        ctx.set_source_rgba(
            *ColorTools.to_rgba_source(ColorTools.COLOR_2)
        )
        histo = self.histogram[0]
        histo_indexes = np.argsort(histo)
        c = 0
        for note in histo_indexes[::-1]:
            if note > 12:
                y = self.to_image_dim(note, 'path_y')
                ctx.move_to(0, y + self.PADDING)
                ctx.line_to(self.rects()['path'][2], y + self.PADDING)
                c = c + 1
                if c > leaders:
                    break
        ctx.set_source_rgba(
            *ColorTools.to_rgba_source(ColorTools.COLOR_4)
        )
        ctx.stroke()
        return surface

    def cairo_draw_path(self):
        """
        Draw the path that connects the estimations
        """
        path_color = ColorTools.to_rgba_source(ColorTools.COLOR_4)
        surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,
            self.rects()['path'][2] + 2 * self.PADDING,
            self.rects()['path'][3] + 2 * self.PADDING
        )
        ctx = cairo.Context(surface)
        ctx.set_source_rgba(*path_color)
        ctx.set_line_width(3)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        for x, y in enumerate(self.samples):
            if y != self.no_value and y != 0.0:
                x1 = self.PADDING + self.to_image_dim(x, 'path_x')
                y1 = self.PADDING + self.to_image_dim(y, 'path_y')
                ctx.line_to(x1, y1)
        ctx.stroke()
        return surface

    def cairo_set_source(self, ctx, surface, x, y):
        ctx.set_source_surface(surface, x, y)
        ctx.paint()

    def cairo_add_background(self, ctx):
        self.cairo_set_source(
            ctx,
            self.cairo_draw_canvas(),
            self.rects()['path'][0],
            self.rects()['path'][1]
        )
        if self.DRAW_GRID:
            self.cairo_set_source(
                ctx,
                self.cairo_draw_grid(),
                self.rects()['path'][0],
                self.rects()['path'][1]
            )
        self.cairo_set_source(
            ctx,
            self.cairo_draw_benchmarks(),
            self.rects()['path'][0],
            self.rects()['path'][1]
        )
        self.cairo_set_source(
            ctx,
            self.cairo_draw_path(),
            self.rects()['path'][0],
            self.rects()['path'][1]
        )
        self.cairo_set_source(
            ctx,
            self.cairo_draw_circles(),
            self.rects()['path'][0],
            self.rects()['path'][1]
        )
        self.cairo_set_source(
            ctx,
            self.cairo_draw_rects(),
            self.rects()['path'][0],
            self.rects()['path'][1]
        )
        self.cairo_set_source(
            ctx,
            self.cairo_draw_text(),
            self.rects()['text'][0],
            self.rects()['text'][1]
        )

    def make_images(self):
        self.images = []
        for x, y in enumerate(self.samples):
            surface_join = cairo.ImageSurface(
                cairo.FORMAT_ARGB32, self.WIDTH, self.HEIGHT
            )
            ctx = cairo.Context(surface_join)
            ctx.rectangle(0, 0, self.WIDTH, self.HEIGHT)
            ctx.set_source_rgba(*ColorTools.to_rgba_source(ColorTools.COLOR_0))
            ctx.fill()
            # Add the background
            self.cairo_add_background(ctx)
            # Add the foreground
            if y != self.no_value and y != 0.0:
                x1 = self.PADDING + \
                    self.to_image_dim(x, 'path_x') + \
                    self.rects()['path'][0]
                y1 = self.PADDING + \
                    self.to_image_dim(y, 'path_y') + self.rects()['path'][1]
                ctx.arc(x1, y1, 15, 0, 2 * math.pi)
                ctx.set_source_rgba(
                    *ColorTools.to_rgba_source(ColorTools.COLOR_10)
                )
                ctx.fill()
            self.images.append(surface_join)
        return self.images

    def cairo_draw_text(self):
        surface_text = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,
            self.rects()['text'][2], self.rects()['text'][3])
        ctx = cairo.Context(surface_text)
        ctx.set_source_rgba(*ColorTools.to_rgba_source(ColorTools.COLOR_8))
        ctx.set_font_size(120)
        ctx.select_font_face(
            "Roboto",
            cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_NORMAL
        )
        (x, y, width, height, dx, dy) = ctx.text_extents(self.data['title'])
        ctx.move_to(self.PADDING,  height + self.PADDING)
        ctx.show_text(self.data['title'])
        return surface_text

    def save_images(self, targetdir=None):
        """
        Save the images and return the pattern able to retrieve them
        """
        self.init_targetdir(targetdir)
        if not self.images:
            self.make_images()
        for x, image in enumerate(self.images):
            imagepath = self.target_path(self.PATTERN % x)
            image.write_to_png(imagepath)
        return self.target_path(self.PATTERN)
