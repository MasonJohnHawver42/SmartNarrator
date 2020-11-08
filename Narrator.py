from pygame import gfxdraw
import pyclipper
import numpy as np
import pygame
import math
import timeit
import tkinter as tk

class Rect:
    def __init__(self, size = (1., 1.), pos = (0., 0.), color = (0, 0, 0)):
        self.size = np.array(size)
        self.pos = np.array(pos) # center
        self.size = self.size.astype(np.float64)
        self.pos = self.pos.astype(np.float64)

        self.color = color

    def getCenter(self):
        return self.pos - (self.size / 2)

    def getPoints(self):
        points = None
        masks = np.array([[-1, 1], [1, 1], [1, -1], [-1, -1]])

        for mask in masks:
            point = self.pos + ((mask / 2.) * self.size)
            if points is None:
                points = np.array([point])
            else:
                points = np.append([point], points, axis=0)

        return points

    def getPoly(self):
        pos = np.array(self.pos)
        self.pos -= pos
        #print(self.pos)
        poly = Poly(self.getPoints(), pos, self.color)
        self.pos += pos

        return poly

    def shift(self, s):
        self.pos -= s

    def scale(self, s):
        self.pos *= s
        self.size *= s

    def draw(self, display):
        center = self.pos - (self.size / 2)
        #pygame.gfxdraw.rect(display, self.color, pygame.Rect(center, self.size))


def rot(p, a):
    point = np.array([(p[0] * math.cos(a)) - (p[1] * math.sin(a)),
                      (p[1] * math.cos(a)) + (p[0] * math.sin(a))])

    return point

def getAngle(point, center = np.array([0, 0])):
    point -= center
    ra = math.pi / 2
    if point[0] == 0:
        return ra * (-1 if point[1] < 0 else 1)
    a = math.atan(point[1] / point[0]) + ra + (ra if point[0] < 0 else -ra)
    point += center

    return a

def getMag(point):
    return math.sqrt((point[0]**2) + (point[1]**2))

def addMag(point, mag):
    pm = getMag(point)
    point /= pm
    point *= pm + mag

def setMag(point, mag):
    pm = getMag(point)
    point /= pm
    point *= mag

def midPoint(p1, p2):
    return (p1 + p2) / 2.0


class Poly:
    def __init__(self, points = Rect().getPoints(), pos = (0, 0), color = (0, 0, 0)):
        self.points = np.array(points)
        self.pos = np.array(pos)
        self.points = self.points.astype(np.float64)
        self.pos = self.pos.astype(np.float64)

        self.color = color

        self.outline = .08

        self.dir = 0

    def rotate(self, a):
        for i, point in enumerate(self.points):
            self.points[i] = rot(point, a)

        self.dir += a

        return self

    def getDir(self):
        return self.dir#getAngle(midPoint(self.points[0], self.points[6 % (len(self.points) - 1)]))

    def setDir(self, d):
        sd = self.getDir()
        self.rotate(-sd + d)

        return self

    def getCenter(self):
        return np.mean(self.points, axis=0)


    def scale(self, s):
        for point in self.points:
            point += self.pos
            point *= s
            point -= self.pos

        return self

    def shift(self, s):
        self.pos -= s

        return self

    def draw(self, display):
        points = []
        for point in self.points:
            points.append([point[0] + self.pos[0], point[1] + self.pos[1]])

        if self.outline:
            pco = pyclipper.PyclipperOffset()
            pco.AddPath(points, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)

            outline = pco.Execute(self.outline * (min(pygame.display.get_surface().get_size()) / 10))[0]

            pygame.draw.polygon(display, (0, 0, 0), outline)

        pygame.draw.polygon(display, self.color, points)

class Viewer:
    def __init__(self):
        self.display = pygame.display.set_mode((800, 800))
        self.viewing_area = Rect((10, 10), (-5, -6))

    def clear(self):
        self.display.fill((100, 180, 110))

    def draw(self, things):
        shift = np.array(self.viewing_area.pos)
        scale = np.array(self.display.get_size()) / np.array(self.viewing_area.size)

        #print(shift, scale, np.array(self.display.get_size()))

        for thing in things:
            thing.shift(shift)
            thing.scale(scale)
            thing.draw(self.display)

        shift *= -1
        scale = 1 / scale

        for thing in things:
            thing.scale(scale)
            thing.shift(shift)

    def render(self):
        pygame.display.update()

class Narrator:
    def __init__(self, pos = (0, -30)):

        self.snapshots = []
        self.snapshot_frame = 0

        self.dt = 0
        self.t = timeit.default_timer()

        self.viewer = Viewer()

        self.pos = np.array(pos)
        self.pos = self.pos.astype(np.float64)

        self.body = Rect((1, 3), self.pos, color = (51, 51, 51))

        points = np.array([ [1/3., 0],
                            [.1,.26],
                            [.2,.285],
                            [.095,.31],
                            [.0625,.77],
                            [.138,.795],
                            [.05,.82],
                            [.15,1]])

        points[:,1] -= .5
        points *= 2.8
        flip = np.array([points[:, i] for i in range(len(points[0]))])[:,::-1]
        flip[0] *= -1
        flip = np.array([flip[:, i] for i in range(len(flip[0]))])
        points = np.append(flip, points, axis=0)
        points[:,1] *= -1

        self.queen_body = Poly(points, self.pos, color = (51, 51, 51))

        self.head = Poly(Rect((1, 1)).getPoints(), (0, 0), color = (51, 51, 51))

        self.head_escalation = .8
        self.head_shift = 0
        self.head_rotation = 0


        self.crown_size = 1.2
        crown_points = [[0, 0],
                        [0, 3 / 4.],
                        [1 / 4., 2 / 4.],
                        [1 / 2., 3 / 4.],
                        [3 / 4., 2 / 4.],
                        [1, 3 / 4.],
                        [1, 0]]

        crown_points = np.array(crown_points)

        for i in range(len(crown_points)):
            p = crown_points[i]
            crown_points[i] = ((p * self.crown_size) - (self.crown_size / 2.)) * np.array([1, -1])

        self.crown = Poly(crown_points, color = (255, 215, 0))

        self.eye_size = .15
        self.eye_openess = [1, 1]
        size = (self.eye_size, self.eye_size)
        color = (255, 255, 255)

        self.eyes = [Rect(size, color = color).getPoly(), Rect(size, color = color).getPoly()]
        self.eyes[0].outline = .06
        self.eyes[1].outline = .06

        self.mouth_width = .3
        self.mouth_height = .1
        self.mouth_openess = [1, 1]
        self.smile_amt = 0

        self.mouth_escalation = .6

        size = (self.mouth_width, self.mouth_height)

        self.mouth = Rect(size, color = color).getPoly()
        self.mouth.outline = .06
        self.setMouth()

        self.eb_rotatioins = [.1, -.1]
        self.eb_width = .32
        self.eb_height = .03
        self.eb_escalations = [.3, .3]

        size = (self.eb_width, self.eb_height)

        self.eye_brows = [Rect(size, color = color).getPoly(), Rect(size, color = color).getPoly()]
        self.eye_brows[0].outline = .06
        self.eye_brows[1].outline = .06

        self.control = Control(self)
        self.control_on = 1

    def loadSnapshot(self, file):
        pass

    def takeFacialSnapshot(self):
        snap = FacialSnapshot()
        snap.takeSnapshot(self)
        return snap

    def applyFacialSnapshot(self, snapshot):
        target_snap = snapshot
        current_snap = FacialSnapshot()
        current_snap.takeSnapshot(self)

        diff = target_snap.getValues() - current_snap.getValues()
        new_vals = current_snap.getValues() + (diff * self.dt * 1)

        if abs(np.sum(diff)) > .001:
            current_snap.setValues(new_vals)
            current_snap.applyFacialSnapshot(self)

            return 1

        else:
            return 0

    def addSnapshot(self, snapshot):
        self.snapshots.append(snapshot)
        print("added")

    def applySnapshots(self):

        if len(self.snapshots) > self.snapshot_frame:
            current = self.snapshots[self.snapshot_frame]
            done = 1 - self.applyFacialSnapshot(current)

            if done:
                self.snapshot_frame += 1

        else:
            if len(self.snapshots) > 0:
                self.snapshots[0].applyFacialSnapshot(self)
                self.snapshot_frame = 0

    def setMouth(self):

        res = 10

        def smile(x):
            return self.smile_amt * (x * x)

        jump = 1. / res
        indexes = np.arange(-1, 1 + jump, jump)
        x1 = indexes * self.mouth_width * self.mouth_openess[0]
        y1 = smile(x1) - (self.mouth_height * self.mouth_openess[1] / 2.0)
        y2 = y1 + (self.mouth_height * self.mouth_openess[1] / 2.0)

        x = np.append(x1, x1[::-1])
        y = np.append(y1, y2)

        self.mouth.points = np.array([(x[i], y[i]) for i in range(len(x))])
        self.mouth.dir = 0

    def start(self):
        self.t = timeit.default_timer()

    def update(self):

        self.head.pos[1] = self.body.pos[1] + (((self.body.size[1] / 2.0) + self.head_escalation) * -1 )
        self.head.pos[0] = self.body.pos[0] + self.head_shift

        self.queen_body.pos = self.body.pos

        self.head.setDir(self.head_rotation)

        frontal_pos = midPoint(self.head.points[0], self.head.points[1])
        side_pos = midPoint(self.head.points[1], self.head.points[2])

        crown_pos = np.array(frontal_pos)
        addMag(crown_pos, (self.crown_size / 1.4))
        crown_pos += self.head.pos
        self.crown.pos = crown_pos
        self.crown.setDir(self.head_rotation)

        eye_central_pos = np.array(frontal_pos)
        eye_central_pos /= 6
        eye_central_pos += self.head.pos

        dis = 2.2

        right = np.array(side_pos) / dis
        left = np.array(side_pos) / -dis

        size = (self.eye_size, self.eye_size * self.eye_openess[0])
        self.eyes[0].points = Rect(size).getPoints()
        self.eyes[0].dir = 0

        self.eyes[0].pos = eye_central_pos + right
        self.eyes[0].setDir(self.head_rotation)

        size = (self.eye_size, self.eye_size * self.eye_openess[1])
        self.eyes[1].points = Rect(size).getPoints()
        self.eyes[1].dir = 0

        self.eyes[1].pos = eye_central_pos + left
        self.eyes[1].setDir(self.head_rotation)

        self.setMouth()

        mouth_pos = np.array(frontal_pos)
        mouth_pos *= -self.mouth_escalation
        mouth_pos += self.head.pos

        self.mouth.pos = mouth_pos
        self.mouth.setDir(self.head_rotation)

        eb_cpr = np.array(eye_central_pos)
        eb_cpr -= self.head.pos
        addMag(eb_cpr, self.eb_escalations[0])
        eb_cpr += self.head.pos

        eb_cpl = np.array(eye_central_pos)
        eb_cpl -= self.head.pos
        addMag(eb_cpl, self.eb_escalations[1])
        eb_cpl += self.head.pos


        self.eye_brows[0].pos = eb_cpr + right
        self.eye_brows[0].setDir(self.head_rotation)
        self.eye_brows[0].rotate(self.eb_rotatioins[0])

        self.eye_brows[1].pos = eb_cpl + left
        self.eye_brows[1].setDir(self.head_rotation)
        self.eye_brows[1].rotate(self.eb_rotatioins[1])


        #self.head_rotation += math.pi / 3000

    def render(self):
        self.viewer.clear()
        self.body.pos *= 0
        body = self.body.getPoly()
        self.viewer.draw([self.queen_body, self.head, self.crown, self.mouth] + self.eyes + self.eye_brows)
        self.viewer.render()

    def edit(self):
        self.start()

        while self.control.cont:
            self.t = timeit.default_timer()
            self.control.update()
            self.control.update_info()
            self.update()
            self.render()
            self.dt = timeit.default_timer() - self.t

    def play(self):
        self.start()
        if len(self.snapshots) > 0:
            self.snapshots[0].applyFacialSnapshot(self)

        while 1:
            self.t = timeit.default_timer()
            self.applySnapshots()
            self.update()
            self.render()
            self.dt = timeit.default_timer() - self.t


        #self.world.viewer.draw([self.crown])

class FacialSnapshot:
    def __init__(self):
        self.facial_data = {"hr": 0, "he": 0, "hs": 0, "mw": 0, "mh": 0, "me": 0, "sa": 0, "es": 0, "reo": 0, "leo": 0, "rbe": 0, "lbe": 0, "rbr": 0, "lbr": 0}

    def takeSnapshot(self, narrator):
        #names = ["hr", "he", "hs", "mw", "mh", "me", "sa", "es", "reo", "leo", "rbe", "lbe", "rbr", "lbr"]
        values = [narrator.head_rotation,
                  narrator.head_escalation,
                  narrator.head_shift,
                  narrator.mouth_width,
                  narrator.mouth_height,
                  narrator.mouth_escalation,
                  narrator.smile_amt,
                  narrator.eye_size,
                  narrator.eye_openess[0],
                  narrator.eye_openess[1],
                  narrator.eb_escalations[0],
                  narrator.eb_escalations[1],
                  narrator.eb_rotatioins[0],
                  narrator.eb_rotatioins[1]]

        self.setValues(values)

    def applyFacialSnapshot(self, narrator):
        narrator.head_rotation = self.facial_data["hr"]
        narrator.head_escalation = self.facial_data["he"]
        narrator.head_shift = self.facial_data["hs"]
        narrator.mouth_width = self.facial_data["mw"]
        narrator.mouth_height = self.facial_data["mh"]
        narrator.mouth_escalation = self.facial_data["me"]
        narrator.smile_amt = self.facial_data["sa"]
        narrator.eye_size = self.facial_data["es"]
        narrator.eye_openess[0] = self.facial_data["reo"]
        narrator.eye_openess[1] = self.facial_data["leo"]
        narrator.eb_escalations[0] = self.facial_data["rbe"]
        narrator.eb_escalations[1] = self.facial_data["lbe"]
        narrator.eb_rotatioins[0] = self.facial_data["rbr"]
        narrator.eb_rotatioins[1] = self.facial_data["lbr"]

    def getValues(self):
        return np.array(list(self.facial_data.values()))

    def setValues(self, values):
        for value, name in zip(values, self.facial_data):
            self.facial_data[name] = value

class Control(tk.Frame):
    def __init__(self, narrator, master=None):
        tk.Frame.__init__(self, master, width=768, height=576, bg="", colormap="new")
        self.grid()
        self.narrator = narrator
        self.createWidgets()
        self.cont = 1

        self.snap = FacialSnapshot()
        self.snap.takeSnapshot(self.narrator)

    def takeSnapshot(self):
        self.snap = self.narrator.takeFacialSnapshot()

    def applySnapshot(self):
        self.narrator.addSnapshot(self.snap)

    def quit(self):
        self.cont = 0

    def createWidgets(self):

        self.div0 = tk.Label(self, text = "\nHead" )

        self.hr_scale = tk.Scale(self, from_=-math.pi / 2., to=math.pi / 2., orient=tk.HORIZONTAL, length = 400, resolution=0.01)
        self.hr_label = tk.Label(self, text = "Head Rotation" )
        self.he_scale = tk.Scale(self, from_=0, to=2, orient=tk.HORIZONTAL, length = 400, resolution=0.01)
        self.he_label = tk.Label(self, text = "Head Elavation" )
        self.hs_scale = tk.Scale(self, from_=-1, to=1, orient=tk.HORIZONTAL, length = 400, resolution=0.01)
        self.hs_label = tk.Label(self, text = "Head Shift" )

        self.div1 = tk.Label(self, text = "\nMouth" )

        self.mw_scale = tk.Scale(self, from_=.05, to=.5, orient=tk.HORIZONTAL, length = 400, resolution=0.01)
        self.mw_label = tk.Label(self, text = "Mouth Width" )
        self.mh_scale = tk.Scale(self, from_=.05, to=.5, orient=tk.HORIZONTAL, length = 400, resolution=0.01)
        self.mh_label = tk.Label(self, text = "Mouth Height" )
        self.me_scale = tk.Scale(self, from_= .5, to= 1.5, orient=tk.HORIZONTAL, length = 400, resolution=0.01)
        self.me_label = tk.Label(self, text = "Mouth Escalation" )
        self.sa_scale = tk.Scale(self, from_= -2, to= 2, orient=tk.HORIZONTAL, length = 400, resolution=0.01)
        self.sa_label = tk.Label(self, text = "Smile Amt" )

        self.div2 = tk.Label(self, text = "\nEyes" )

        self.es_scale = tk.Scale(self, from_= .1, to= .5, orient=tk.HORIZONTAL, length = 400, resolution=0.001)
        self.es_label =  tk.Label(self, text = "Eye Size" )
        self.eor_scale = tk.Scale(self, from_= .1, to= 1.5, orient=tk.HORIZONTAL, length = 400, resolution=0.001)
        self.eor_label = tk.Label(self, text = "Right Eye Openess" )
        self.eol_scale = tk.Scale(self, from_= .1, to= 1.5, orient=tk.HORIZONTAL, length = 400, resolution=0.001)
        self.eol_label = tk.Label(self, text = "Left Eye Openess" )

        self.div3 = tk.Label(self, text = "\nEye Brows" )

        self.ber_scale = tk.Scale(self, from_= 0, to= .5, orient=tk.HORIZONTAL, length = 400, resolution=0.01)
        self.ber_label = tk.Label(self, text = "Right Eye Brow Escalation" )
        self.bel_scale = tk.Scale(self, from_= 0, to= .5, orient=tk.HORIZONTAL, length = 400, resolution=0.01)
        self.bel_label = tk.Label(self, text = "Left Eye Brow Escalation" )
        self.brr_scale = tk.Scale(self, from_= -math.pi / 6., to= math.pi / 6., orient=tk.HORIZONTAL, length = 400, resolution=.01)
        self.brr_label = tk.Label(self, text = "Right Eye Brow Rotation" )
        self.brl_scale = tk.Scale(self, from_= math.pi / 6., to= -math.pi / 6., orient=tk.HORIZONTAL, length = 400, resolution=.01)
        self.brl_label = tk.Label(self, text = "Left Eye Brow Rotation" )

        self.div4 = tk.Label(self, text = "\n" )

        self.applySnapshot = tk.Button(self, text='addSnapshot', command=self.applySnapshot)
        self.takeSnapshot = tk.Button(self, text='takeSnapshot', command=self.takeSnapshot)
        self.quitButton = tk.Button(self, text='Quit', command=self.quit)

        self.div0.grid(row=0, column=1)

        self.hr_scale.grid(row=1, column=1)
        self.hr_label.grid(row=1, column=0)
        self.he_scale.grid(row=2, column=1)
        self.he_label.grid(row=2, column=0)
        self.hs_scale.grid(row=3, column=1)
        self.hs_label.grid(row=3, column=0)

        self.div1.grid(row=4, column=1)

        self.mw_scale.grid(row=5, column=1)
        self.mw_label.grid(row=5, column=0)
        self.mh_scale.grid(row=6, column=1)
        self.mh_label.grid(row=6, column=0)
        self.me_scale.grid(row=7, column=1)
        self.me_label.grid(row=7, column=0)
        self.sa_scale.grid(row=8, column=1)
        self.sa_label.grid(row=8, column=0)

        self.div2.grid(row=9, column=1)

        self.es_scale.grid(row=10, column=1)
        self.es_label.grid(row=10, column=0)
        self.eor_scale.grid(row=11, column=1)
        self.eor_label.grid(row=11, column=0)
        self.eol_scale.grid(row=12, column=1)
        self.eol_label.grid(row=12, column=0)

        self.div3.grid(row=13, column=1)

        self.ber_scale.grid(row=14, column=1)
        self.ber_label.grid(row=14, column=0)
        self.bel_scale.grid(row=15, column=1)
        self.bel_label.grid(row=15, column=0)
        self.brr_scale.grid(row=16, column=1)
        self.brr_label.grid(row=16, column=0)
        self.brl_scale.grid(row=17, column=1)
        self.brl_label.grid(row=17, column=0)

        self.div4.grid(row=18, column=0)

        self.takeSnapshot.grid(row=19, column=0)
        self.applySnapshot.grid(row=19, column=1)
        self.quitButton.grid(row=19, column=2)

        self.set_vals()

    def set_vals(self):
        self.hr_scale.set(self.narrator.head_rotation)
        self.he_scale.set(self.narrator.head_escalation)
        self.hs_scale.set(self.narrator.head_shift)
        self.mw_scale.set(self.narrator.mouth_width)
        self.mh_scale.set(self.narrator.mouth_height)
        self.me_scale.set(self.narrator.mouth_escalation)
        self.sa_scale.set(self.narrator.smile_amt)
        self.es_scale.set(self.narrator.eye_size)
        self.eor_scale.set(self.narrator.eye_openess[0])
        self.eol_scale.set(self.narrator.eye_openess[1])
        self.ber_scale.set(self.narrator.eb_escalations[0])
        self.bel_scale.set(self.narrator.eb_escalations[1])
        self.brr_scale.set(self.narrator.eb_rotatioins[0])
        self.brl_scale.set(self.narrator.eb_rotatioins[1])

        #self.update()
        #self.after(10, self.update_info)

    def update_info(self):
        #print("here")
        self.narrator.head_rotation = self.hr_scale.get()
        self.narrator.head_escalation = self.he_scale.get()
        self.narrator.head_shift = self.hs_scale.get()
        self.narrator.mouth_width = self.mw_scale.get()
        self.narrator.mouth_height = self.mh_scale.get()
        self.narrator.mouth_escalation = self.me_scale.get()
        self.narrator.smile_amt = self.sa_scale.get()
        self.narrator.eye_size = self.es_scale.get()
        self.narrator.eye_openess[0] = self.eor_scale.get()
        self.narrator.eye_openess[1] = self.eol_scale.get()
        self.narrator.eb_escalations[0] = self.ber_scale.get()
        self.narrator.eb_escalations[1] = self.bel_scale.get()
        self.narrator.eb_rotatioins[0] = self.brr_scale.get()
        self.narrator.eb_rotatioins[1] = self.brl_scale.get()

        #self.after(10, self.update_info)

qn = Narrator()
qn.edit()
print("end")
qn.play()
