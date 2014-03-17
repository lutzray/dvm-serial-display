# -*- coding: utf-8 -*-
#import serial
import math
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import random
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

try:
    import serial
except ImportError:
    WITH_SERIAL = False
else:
    WITH_SERIAL = True

GOAL_VALUE = 250

SIMULATED_VALUE = 0.05  # modifié pour partir a zéro
DEL_SIMULATED = 0.005   
RANDOM_WALK_CRIT = 0.33 # probabilite de descendre
# parmètres utilisés
# pour simuler le port série
# lorsque l'appareil n'est pas branché, cf read_volts_without_serial()


MIN_GRAPH = 0   # modifié pour partir a zéro
GRAPH_MAX_FORCE_INIT = 400  # modifié
GRAPH_FORCE_MAX_MARGIN = 0.15 # 15%
GRAPH_WIDTH = 100


PROMPT_SEQU = '\r\n=>\r\n'
# séquence de caractères envoyés par le multimètre pour
# signaler la complétion de la commande.
#
# http://www.bkprecision.com/downloads/manuals/en/5491A_manual.pdf
# p.51 Table 6-2. "RS-232 Return Prompts"
# <RESULT> + <CR> <LF> + <PROMPT> + <CR><LF>
# "=>" A command is executed and no errors are detected

def read_volts_without_serial():
    global SIMULATED_VALUE
    if random.random() > RANDOM_WALK_CRIT:
        SIMULATED_VALUE += DEL_SIMULATED
    else:
        SIMULATED_VALUE -= DEL_SIMULATED
    return SIMULATED_VALUE
        
def read_volts():
    if not WITH_SERIAL: return read_volts_without_serial()
    ser.write('R1\r\n')
    # envoie la demande de lecture
    #
    # After executing R1 command, the meter will return the 
    # current readings in its primary display.
    # For example, a returned character string “+110.234E+0” represents
    # the primary display reading  “+110.234”
    # op.cit. p.61
    received_string = ''
    while True:
        buff = ser.read()
        if not buff:
            print 'rien'
            continue
        received_string = received_string + buff
        if received_string.endswith(PROMPT_SEQU):
            voltage = float(received_string.split(PROMPT_SEQU)[0])
            # received string moins la chaîne PROMPT_SEQU
            break
    return voltage

def to_lbs(volts):
    V0 = 0.060
    psi = (volts-V0)*1000
    A= math.pi
    F=A*psi
    return F

#def display_current(val):
#    ax.text(0.3, 0.5, "%6.0f lbs" %val, family ='monospace', fontsize=20,
#            bbox={'facecolor':'white', 'pad':10}, transform=ax.transAxes)

def display_max(val):
    ax.text(0.65, 0.03, "%6.0f lbs max" %val, family ='monospace', fontsize=20,
            bbox={'facecolor':'white', 'pad':10}, transform=ax.transAxes)

def close_port_quit(self):
    global END_LOOP # l'utilisation de global est un hack inéléguant...
    END_LOOP = True
    plt.close()

def reset_max(self):
    global force_max
    force_max = 0

if WITH_SERIAL:
    ser = serial.Serial(rtscts=True, timeout=1)
    ser.baudrate = 9600
    ser.port = 0
    ser.open()


fig = plt.figure()
fig.subplots_adjust(bottom=0.2)
ax = fig.add_subplot(111)
ax.get_xaxis().set_visible(False)
line1 = Line2D([], [], color='black', linewidth=2)
line1.set_linestyle('None')
line1.set_marker('o')
ax.add_line(line1)
#ax.set_ylim(MIN_GRAPH, GRAPH_MAX_FORCE_INIT)
#ax.set_xlim(0,GRAPH_WIDTH)
rect = Rectangle( (0, GOAL_VALUE), width=GRAPH_WIDTH, height=10) #todo : height relatif
ax.add_patch(rect)

plt.ion()

axRAZ = plt.axes([0.4, 0.05, 0.2, 0.075])
axClose = plt.axes([0.65, 0.05, 0.3, 0.075])
bRAZ = Button(axRAZ, 'RAZ valeur max')
bRAZ.on_clicked(reset_max)
bClose = Button(axClose, u'Clore le port série et quitter')
bClose.on_clicked(close_port_quit)

forces = []
force_max=0
END_LOOP = False
while not END_LOOP:
    force = to_lbs(read_volts())
    force_max = max(force, force_max) #plus compact que if then
    display_max(force_max)
    graph_max_force = max(GRAPH_MAX_FORCE_INIT, force_max*(1 + GRAPH_FORCE_MAX_MARGIN) )
    ax.set_ylim(MIN_GRAPH, graph_max_force)
    ax.set_xlim(0, GRAPH_WIDTH)
    forces.append(force)
    line1.set_ydata(forces) 
    x = range(len(forces))
    line1.set_xdata(x)
    plt.draw()
    if len(forces) > GRAPH_WIDTH:
        forces = []

#    if force_max > 250:    # ajout -> 250?
#        GRAPH_MAX_FORCE_INIT = force_max + 100 #ajout pour auto ajustement de l'axe y
#    display_current(force)

#    time.sleep(0.05) #choke
    plt.pause(0.1)

if WITH_SERIAL:
    ser.close()

