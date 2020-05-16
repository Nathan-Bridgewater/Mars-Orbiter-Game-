"""
A game where the user controls a satellite and needs to fix the orbital
trajectory in order map the soil moisture on Mars. Use the arrow keys to fire
thrusters and control the Dx and Dy components of the satellite, avoid running
out of fuel or burning up in the atmosphere
"""
import os
import math
import random
import pygame as pg

# build a colour table
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
LT_BLUE = (173, 216, 230)


class Satellite(pg.sprite.Sprite):
    """Satellite object that rotates to face a planet, can crash and burn."""

    def __init__(self, background):
        super().__init__()
        self.background = background
        # load two satellite images, assign one as the default and get position
        self.image_sat = pg.image.load("satellite.png").convert()
        self.image_crash = pg.image.load("satellite_crash_40x33.png").convert()
        self.image = self.image_sat
        self.rect = self.image.get_rect()
        self.image.set_colorkey(BLACK)  # sets transparent colour for background

        # set initial x y coordinates at random as well as velocity
        self.x = random.randrange(315, 425)
        self.y = random.randrange(70, 180)
        self.dx = random.choice([-3, 3])
        self.dy = 0
        self.heading = 0  # initialise dish orientation
        self.fuel = 100
        self.mass = 1
        self.distance = 0  # initialise distance between satellite and planet
        self.thrust = pg.mixer.Sound('thrust_audio.ogg')
        self.thrust.set_volume(0.07)  # valid values are 0-1

    def thruster(self, dx, dy):
        """Execute actions associated with firing the thrusters"""
        self.dx += dx  # change tangential velocity
        self.dy += dy  # change velocity in the direction of the planet
        self.fuel -= 2  # reduce fuel in tank
        self.thrust.play()  # play sound

    def check_keys(self):
        """Check if user presses arrow keys and call thruster method."""
        keys = pg.key.get_pressed()
        # fire thrusters by changing dx/dy dependant on arrow keys pressed
        if keys[pg.K_RIGHT]:
            self.thruster(dx=0.05, dy=0)
        elif keys[pg.K_LEFT]:
            self.thruster(dx=-0.05, dy=0)
        elif keys[pg.K_UP]:
            self.thruster(dx=0, dy=-0.05)
        elif keys[pg.K_DOWN]:
            self.thruster(dx=0, dy=0.05)

    def locate(self, planet):
        """Calculate distance and heading to planet"""
        # subtract planet x/y coordinates from satellite coordinates
        px, py = planet.x, planet.y
        dist_x = self.x - px
        dist_y = self.y - py
        # get angle/heading between satellite and planet
        planet_dir_radians = math.atan2(dist_x, dist_y)
        self.heading = planet_dir_radians * 180 / math.pi  # pygame uses degrees
        # rotate the satellite image 90 clockwise to have it facing the planet
        self.heading -= 90
        self.distance = math.hypot(dist_x, dist_y)

    def rotate(self):
        """Rotate satellite using degrees so dish faces planet."""
        # rotate using heading from location and get rect values
        self.image = pg.transform.rotate(self.image_sat, self.heading)
        self.rect = self.image.get_rect()

    def path(self):
        """Update satellite's position and draw line to trace orbital path"""
        # add values from thruster to old position
        last_center = (self.x, self.y)
        self.x += self.dx
        self.y += self.dy
        # draw between old and new points
        pg.draw.line(self.background, WHITE, last_center, (self.x, self.y))

    def update(self):
        """Update satellite object during the game"""
        self.check_keys()
        self.rotate()
        self.path()
        self.rect.center = (self.x, self.y)
        # change image to burning satellite if in planets atmosphere
        if self.dx == 0 and self.dy == 0:
            self.image = self.image_crash
            self.image.set_colorkey(BLACK)


class Planet(pg.sprite.Sprite):
    """Planet object that rotates and projects a gravity field."""

    def __init__(self):
        super().__init__()
        # load images and copy so master does not get degraded in transformation
        self.image_mars = pg.image.load("mars.png").convert()
        self.image_water = pg.image.load("mars_water.png").convert()
        self.image_copy = pg.transform.scale(self.image_mars, (100, 100))
        self.image_copy.set_colorkey(BLACK)
        self.rect = self.image_copy.get_rect()
        self.image = self.image_copy
        self.mass = 2000
        self.x = 400
        self.y = 320
        self.rect.center = (self.x, self.y)
        # define an angle for the planets angle and the rate of rotation
        self.angle = math.degrees(0)
        self.rotate_by = math.degrees(0.01)

    def rotate(self):
        """Rotate the planet image with each game loop."""
        last_center = self.rect.center
        # rotate image to the set angle
        self.image = pg.transform.rotate(self.image_copy, self.angle)
        self.rect = self.image.get_rect()
        # recenter due to the bounding rect box changing on rotation
        self.rect.center = last_center
        # increase angle
        self.angle += self.rotate_by

    def gravity(self, satellite):
        """Calculate impact of gravity on the satellite."""
        G = 1.0  # 'gravitational constant for the game
        dist_x = self.x - satellite.x
        dist_y = self.y - satellite.y
        distance = math.hypot(dist_x, dist_y)
        # normalise to a unit vector
        dist_x /= distance
        dist_y /= distance
        # apply gravity
        force = G * (satellite.mass * self.mass) / math.pow(distance, 2)
        satellite.dx += (dist_x * force)
        satellite.dy += (dist_y * force)

    def update(self):
        """Call the rotate method"""
        self.rotate()


def calc_eccentricity(dist_list):
    """Calculate & return eccentricity from list of radii"""
    apoapsis = max(dist_list)  # furthest distance from center of orbit to edge
    periapsis = min(dist_list)  # closest distance from center of orbit to edge
    eccentrcity = (apoapsis - periapsis) / (apoapsis + periapsis)
    return eccentrcity


def instruct_label(screen, text, colour, x, y):
    """Take screen, list of strings, colour & origin & render text to screen"""
    # create font object needed for rendering
    instruct_font = pg.font.SysFont(None, 25)
    line_spacing = 22
    for index, line in enumerate(text):
        # for each new line increase the y value so its further down the screen
        label = instruct_font.render(line, True, colour, BLACK)
        screen.blit(label, (x, y + index * line_spacing))


def box_label(screen, text, dimensions):
    """Make fixed-sized label from screen, text & left, top, width, height"""
    # create font object
    readout_font = pg.font.SysFont(None, 27)
    # create white rectangle to place text on top of
    base = pg.Rect(dimensions)
    pg.draw.rect(screen, WHITE, base, 0)
    # render text and set its center to the center of the base rect
    label = readout_font.render(text, True, BLACK)
    label_rect = label.get_rect(center=base.center)
    screen.blit(label, label_rect)


def mapping_on(planet):
    """Show soil moisture image of planet."""
    # get coordinates of planet centre and scale the new image
    last_center = planet.rect.center
    planet.image_copy = pg.transform.scale(planet.image_water, (100, 100))
    planet.image_copy.set_colorkey(BLACK)  # set background to transparent
    planet.rect = planet.image_copy.get_rect()
    planet.rect.center = last_center  # recenter to avoid wobbling


def mapping_off(planet):
    """Restore normal planet image"""
    planet.image_copy = pg.transform.scale(planet.image_mars, (100, 100))
    planet.image_copy.set_colorkey(BLACK)


def cast_shadow(screen):
    """Add optional terminator and shadow behind planet to screen"""
    shadow = pg.Surface((400, 100), flags=pg.SRCALPHA)
    shadow.fill((0, 0, 0, 210))  # last number sets transparency
    screen.blit(shadow, (0, 270))  # tuple is top left coordinates


def main():
    """set up labels & instructions, create objects & run the game loop."""
    pg.init()  # initialise pygame

    # set up display
    os.environ['SDL_VIDEO_WINDOW_POS'] = '700, 100'  # set game window origin
    screen = pg.display.set_mode((800, 645), pg.FULLSCREEN)
    pg.display.set_caption('Mars Orbiter')
    background = pg.Surface(screen.get_size())  # background object
    pg.mixer.init()

    intro_text = [
        ' The Mars Orbiter experienced an error during Orbit insertion.',
        ' Use thrusters to correct to a circular mapping orbit without',
        ' running out of propellant or burning up in the atmosphere.'
        ]

    instruct_text1 = [
        'Orbital altitude must be within 69 - 120 miles',
        'Orbital Eccentricity must be < 0.05',
        'Avoid top of atmosphere at 68 miles'
        ]
    instruct_text2 = [
        'Left arrow = Decrease Dx',
        'Right arrow = Increase Dx',
        'Up arrow = Increase Dy',
        'Down arrow = Decrease Dy',
        'Space bar = Clear path',
        'Escape = Exit full screen'
    ]

    # instantiate planet and satellite objects
    planet = Planet()
    planet_sprite = pg.sprite.Group(planet)
    sat = Satellite(background)
    sat_sprite = pg.sprite.Group(sat)

    # for circular orbit verification
    dist_list = []
    eccentricity = 1
    eccentricty_calc_interval = 5  # optimised for 120 mile altitude

    # time keeping
    clock = pg.time.Clock()
    fps = 30
    tick_count = 0

    # for soil mapping functionality
    mapping_enabled = False

    running = True
    while running:
        clock.tick(fps)
        tick_count += 1
        dist_list.append(sat.distance)

        # get keyboard input
        for event in pg.event.get():
            if event.type == pg.QUIT:  # close window
                running = False
            elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                screen = pg.display.set_mode((800, 645))
            elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                background.fill(BLACK)  # clear path
            elif event.type == pg.KEYUP:
                sat.thrust.stop()  # stop sound
                mapping_off(planet)
            elif mapping_enabled:
                if event.type == pg.KEYDOWN and event.key == pg.K_m:
                    mapping_on(planet)

        # get heading and distance to planet and apply gravity
        sat.locate(planet)
        planet.gravity(sat)

        # calculate orbital eccentricity
        if tick_count % (eccentricty_calc_interval * fps) == 0:
            eccentricity = calc_eccentricity(dist_list)
            dist_list = []

        # re-blit background for drawing command - prevents clearing path
        screen.blit(background, (0, 0))

        # fuel/ altitude fail conditions
        if sat.fuel <= 0:
            instruct_label(screen, ['Fuel depleted'], RED, 340, 195)
            sat.fuel = 0
            sat.dx = 2

        elif sat.distance <= 68:
            instruct_label(screen, ['Atmospheric entry'], RED, 320, 195)
            sat.dx = 0
            sat.dy = 0

        # enable mapping functionality
        if eccentricity < 0.05 and 69 <= sat.distance <= 120:
            map_instruct = ['Press & hold m to map moisture']
            instruct_label(screen, map_instruct, LT_BLUE, 250, 175)
            mapping_enabled = True
        else:
            mapping_enabled = False

        planet_sprite.update()
        planet_sprite.draw(screen)
        sat_sprite.update()
        sat_sprite.draw(screen)

        # display intro text for 15 seconds
        if pg.time.get_ticks() <= 15000:  # time in milliseconds
            instruct_label(screen, intro_text, GREEN, 145, 100)

        # display telemetry and instructions
        box_label(screen, 'Dx', (70, 20, 75, 20))
        box_label(screen, 'Dy', (150, 20, 80, 20))
        box_label(screen, 'Altitude', (240, 20, 260, 20))
        box_label(screen, 'Fuel', (410, 20, 160, 20))
        box_label(screen, 'Eccentricity', (580, 20, 150, 20))

        box_label(screen, '{:.1f}'.format(sat.dx), (70, 50, 75, 20))
        box_label(screen, '{:.1f}'.format(sat.dy), (150, 50, 80, 20))
        box_label(screen, '{:.1f}'.format(sat.distance), (240, 50, 160, 20))
        box_label(screen, '{}'.format(sat.fuel), (410, 50, 160, 20))
        box_label(screen, '{:.8f}'.format(eccentricity), (580, 50, 150, 20))

        instruct_label(screen, instruct_text1, WHITE, 10, 575)
        instruct_label(screen, instruct_text2, WHITE, 570, 510)

        # add terminator & border
        cast_shadow(screen)
        pg.draw.rect(screen, WHITE, (1, 1, 798, 643), 1)

        pg.display.flip()


if __name__ == '__main__':
    main()
