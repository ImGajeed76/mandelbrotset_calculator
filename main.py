import multiprocessing
from multiprocessing import Process

from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import numba
import pygame
from PIL import Image
from tqdm import tqdm


@numba.jit(nopython=True)
def mandel_pixel(x, y, max_i=100):
    c1 = complex(x, y)
    c2 = 0
    for n in range(max_i):
        c2 = c2 ** 2 + c1
        if abs(c2) > 20000:
            return float(n)
    return float(0)


def calc_mandelbrot_piece(old_width, old_height, old_divider, i, j, q: multiprocessing.Queue = multiprocessing.Queue(),
                          max_i=100):
    width = int(old_width / old_divider)
    height = int(old_height / old_divider)
    pos_x = (i - old_divider / 3) * (old_width / old_divider)
    pos_y = (j - old_divider / 3) * (old_height / old_divider)
    divider = old_width / 5

    if divider is None:
        divider = width / 5

    img = Image.new(mode="RGB", size=(width, height))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            nx = ((x + pos_x - (width / 2)) / divider)
            ny = ((y + pos_y - (height / 2)) / divider)
            n = mandel_pixel(nx, ny, max_i)
            c = (n / 6 * 255)
            pixels[x, y] = (int(c), int(c / 2), int(c / 3))

    q.put(img)
    return img


def calc_mandelbrot(width, height, max_i=100, divider=3):
    if width % 2 != 0 or height % 2 != 0:
        exit("SizeError: width or height not dividable by two")
        return

    img = Image.new(mode="RGB", size=(width, height))
    print(img.size)
    processes = []
    queues: list[multiprocessing.Queue] = []

    for i in tqdm(range(divider), desc="Starting"):
        for j in range(divider):
            q = multiprocessing.Queue()
            queues.append(q)

            p = Process(target=calc_mandelbrot_piece, args=(width, height, divider, i, j, queues[-1], max_i))
            processes.append(p)

            processes[-1].start()

    for i in tqdm(range(divider), desc="Merging"):
        for j in range(divider):
            n_img: Image.Image = queues[i + j * divider].get()

            y = int(i * (height / divider))
            x = int(j * (width / divider))
            img.paste(n_img, (x, y))

    return img


def live_mandelbrot(width, height, max_i=100, down_scale_factor=1):
    pygame.init()
    down_width = int(width * (1 / down_scale_factor))
    down_height = int(height * (1 / down_scale_factor))
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()
    done = False

    speed = 3
    zoom = width / 5

    zooming = 0

    tx = 0
    ty = 0

    ctx = 0
    cty = 0

    while not done:
        print(f"x: {tx}, y: {ty}, z: {zoom}")
        screen.fill((0, 0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    zooming = speed
                elif event.key == pygame.K_q:
                    zooming = -speed
                elif event.key == pygame.K_a:
                    ctx = -speed
                elif event.key == pygame.K_d:
                    ctx = speed
                elif event.key == pygame.K_w:
                    cty = -speed
                elif event.key == pygame.K_s:
                    cty = speed
                elif event.key == pygame.K_ESCAPE:
                    done = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_e:
                    zooming = 0
                elif event.key == pygame.K_q:
                    zooming = 0
                elif event.key == pygame.K_a:
                    ctx = 0
                elif event.key == pygame.K_d:
                    ctx = 0
                elif event.key == pygame.K_w:
                    cty = 0
                elif event.key == pygame.K_s:
                    cty = 0

        zoom += zooming * 3
        tx += ctx + ((tx / zoom) * zooming * 3)
        ty += cty + ((ty / zoom) * zooming * 3)

        for y in range(down_height):
            for x in range(down_width):
                mx = ((x + tx - (down_width / 2)) / zoom)
                my = ((y + ty - (down_height / 2)) / zoom)
                n = mandel_pixel(mx, my, max_i)
                c = int(n / 6 * 255)

                if c > 255:
                    c = 255

                color = [int(c), int(c / 2), int(c / 3)]
                pygame.draw.rect(screen, color, pygame.Rect(x * down_scale_factor, y * down_scale_factor,
                                                            x * down_scale_factor + down_scale_factor - 1,
                                                            y * down_scale_factor + down_scale_factor - 1))

        pygame.draw.line(screen, (255, 255, 255), (width / 2 - 1, height / 2), (width / 2 + 1, height / 2))
        pygame.draw.line(screen, (255, 255, 255), (width / 2, height / 2 - 1), (width / 2, height / 2 + 1))
        clock.tick(60)
        pygame.display.update()

    pygame.quit()


if __name__ == '__main__':
    w = 600
    h = int(w / 1.3333333333333333333333333)
    live_mandelbrot(w, h, down_scale_factor=6)
