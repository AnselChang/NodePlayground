# KEYBOARD HOTKEYS:
#   z -> new node
#   x -> delete
#   a -> change text
#   t -> toggle node/edge
#   s -> generate savefile
#   p -> print c++ code

# pyinstaller nodes.py --onefile

import json 
INPUT = input("Paste save text here, or just press enter to create a new graph:  ").strip()
if INPUT == "":
    print("Loading new graph...")
else:
    print("Loading pasted graph..")
    info = json.loads(INPUT)

import pygame, sys, math, pygame.gfxdraw
from os.path import exists, join

version = "1.3.9"

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    print('running in a PyInstaller bundle', sys._MEIPASS)
    application_path = os.path.dirname(sys.executable)
    print(application_path)
else:
    print('running in a normal Python process')
    application_path = None

pygame.init()
pygame.display.set_caption('NodePlayground by Ansel')
pygame.font.init()

fontHuge = pygame.font.SysFont("Comic Sans Bold", 30)
fontBig = pygame.font.SysFont("Comic Sans Bold", 54)
font = pygame.font.SysFont("Comic Sans Bold", 34)
fontsmall = pygame.font.SysFont("Comic Sans", 24)

WIDTH = 1400
HEIGHT = 820

LINE_RADIUS = 4

LEGAL = "abcdefghijklmnopqrstuvwxyz1234567890-,."

WHITE = [255,255,255]
GREEN = [30,200,30]
RED = [255,70,70]
BLACK = [0,0,0]
YELLOW = [255,255,30]
LINE_COLOR = [180,180,180]


def drawThickLine(surf, color, x1,y1,x2,y2, thickness):
    # https://stackoverflow.com/questions/30578068/pygame-draw-anti-aliased-thick-line
    center_L1 = [(x1+x2) / 2, (y1+y2)/2]
    angle = math.atan2(y1 - y2, x1 - x2)
    length = math.sqrt((y2-y1)**2 + (x2-x1)**2)

    UL = (center_L1[0] + (length/2.) * math.cos(angle) - (thickness/2.) * math.sin(angle),
          center_L1[1] + (thickness/2.) * math.cos(angle) + (length/2.) * math.sin(angle))
    UR = (center_L1[0] - (length/2.) * math.cos(angle) - (thickness/2.) * math.sin(angle),
          center_L1[1] + (thickness/2.) * math.cos(angle) - (length/2.) * math.sin(angle))
    BL = (center_L1[0] + (length/2.) * math.cos(angle) + (thickness/2.) * math.sin(angle),
          center_L1[1] - (thickness/2.) * math.cos(angle) + (length/2.) * math.sin(angle))
    BR = (center_L1[0] - (length/2.) * math.cos(angle) + (thickness/2.) * math.sin(angle),
          center_L1[1] - (thickness/2.) * math.cos(angle) - (length/2.) * math.sin(angle))

    pygame.gfxdraw.aapolygon(surf, (UL, UR, BR, BL), color)
    pygame.gfxdraw.filled_polygon(surf, (UL, UR, BR, BL), color)

def drawCircle(surface, color, pos, radius):
    pygame.gfxdraw.aacircle(surface, *pos, radius, color)
    pygame.gfxdraw.filled_circle(surface, *pos, radius, color)

def blitCenterText(surface, string, font, x, y, highlighted):

    margin = 2
        
    text = font.render(string, True, BLACK if highlighted else WHITE)
    x -= text.get_width()*0.5

    if highlighted:
        pygame.draw.rect(surface, [100,100,200], [x-margin, y-margin, text.get_width() + margin*2, text.get_height() + margin*2])

    surface.blit(text, [x, y])

def distance(x1, y1, x2, y2):
    return ( ( (x2 - x1 )**2) + ((y2-y1)**2) )**0.5

def distanceTwoPoints(x0, y0, x1, y1, x2, y2):
    return abs((x2-x1)*(y1-y0)- (x1-x0)*(y2-y1)) / distance(x1, y1, x2, y2)

def lighten(color, amount, doThis = True):
    if doThis:
        return [min(i * amount,255) for i in color]
    else:
        return color

def shiftPressed():
    return (pygame.key.get_mods() & pygame.KMOD_SHIFT) != 0
    
NONE = 0
ID_HIGHLIGHT = 1
NAME_HIGHLIGHT = 2
TEXT_HIGHLIGHT = 3

class Node:

    def __init__(self, ID, name, text, special, x, y, graph, textList = False):

        if textList == False:
            self.text = [None]*4
            self.text[ID_HIGHLIGHT] = str(ID)
            self.text[NAME_HIGHLIGHT] = name
            self.text[TEXT_HIGHLIGHT] = text
        else:
            self.text = textList
            
        self.special = special
        self.graph = graph

        self.highlight = NONE
        
        self.x = x
        self.y = y
        self.radius = 50
        self.neighbors = []

        self.rank = -1

    def id(self):
        return self.text[ID_HIGHLIGHT]

    def name(self):
        return self.text[NAME_HIGHLIGHT]

    def getText(self):
        return self.text[TEXT_HIGHLIGHT]

    def resetText(self):
        if self.highlight != NONE:
            self.text[self.highlight] = self.text[self.highlight].strip()
        self.highlight = NONE
        if self.text[ID_HIGHLIGHT] == "":
            self.text[ID_HIGHLIGHT] = str(self.graph.nextID())

        self.text[ID_HIGHLIGHT] = str(int(self.text[ID_HIGHLIGHT]))

    def draw(self, screen, darken):
        color = lighten(RED if self.special else GREEN, darken)
        drawCircle(screen, color, [self.x, self.y], self.radius)
        blitCenterText(screen, self.text[ID_HIGHLIGHT], fontBig, self.x, self.y - 45, self.highlight == ID_HIGHLIGHT)
        blitCenterText(screen, self.text[NAME_HIGHLIGHT].upper(), font, self.x, self.y - 10, self.highlight == NAME_HIGHLIGHT)
        blitCenterText(screen, self.text[TEXT_HIGHLIGHT], fontsmall, self.x, self.y + 20, self.highlight == TEXT_HIGHLIGHT)

    def add(self, neighbor):
        self.neighbors.append(neighbor)

    def remove(self, neighbor):
        self.neighbors.remove(neighbor)

    def __str__(self):
        return str(self.ID)

    def save(self, i):
        self.rank = i
        return [self.id(), self.name(), self.getText(), self.special, self.x, self.y]

class Edge:

    def __init__(self, node1, node2, special = False):
        self.node1 = node1
        self.node2 = node2
        self.special = special

    def unlink(self):
        self.node1.neighbors.remove(self.node2)
        self.node2.neighbors.remove(self.node1)
        

    def draw(self, screen, darken):
        color = lighten(YELLOW if self.special else LINE_COLOR, 0.75, darken)
        drawThickLine(screen, color, self.node1.x, self.node1.y, self.node2.x, self.node2.y, LINE_RADIUS*2)

    def save(self):
        return [self.node1.rank, self.node2.rank, self.special]


class Graph:
    def __init__(self):
        self.nodes = []
        self.edges = []

    def exists(self, ID):
        for node in self.nodes:
            if node.id() == str(ID):
                return True
        return False

    def nextID(self):
        ID = 0
        while  self.exists(ID):
            ID += 1
        return ID

    def add(self, ID, name, text, special, x, y):
        
        self.nodes.append(Node(ID, name, text, special, x, y, self))

    def addEdge(self, node1, node2, special = False):

        # duplicate
        if node1 in node2.neighbors:
            return
        
        self.edges.append(Edge(node1, node2, special))
        node1.add(node2)
        node2.add(node1)


    def get(self, x, y):

        for node in self.nodes:
            if distance(x, y, node.x, node.y) < node.radius*1.1:
                 return node
        return None

    def getEdge(self, x, y):
        for edge in self.edges:
            if distanceTwoPoints(x,y, edge.node1.x, edge.node1.y, edge.node2.x, edge.node2.y) <= LINE_RADIUS + 7:
                dist = distance(edge.node1.x, edge.node1.y, edge.node2.x, edge.node2.y)
                if distance(x, y, edge.node1.x, edge.node1.y) < dist and distance(x, y, edge.node2.x, edge.node2.y) < dist:
                    return edge
        
    def delete(self, node):

        if node is None:
            return

        # Delete edges with node
        i = 0
        while i < len(self.edges):
            if node == self.edges[i].node1 or node == self.edges[i].node2:
                self.edges.pop(i)
                i -= 1
            i += 1

        # Remove neighbor relations
        for neighbor in node.neighbors:
            neighbor.neighbors.remove(node)

        # Delete node from nodes
        self.nodes.remove(node)

    def deleteEdge(self, edge):

        if edge is None:
            return

        edge.unlink()
        self.edges.remove(edge)
                


    def draw(self, screen, x, y, nodeHovered, edgeHovered, nodeMoving):

        for edge in self.edges:
            edge.draw(screen, nodeHovered is None and edge == edgeHovered)
        
        for node in reversed(self.nodes):
            node.draw(screen, 0.6 if nodeMoving == node else (0.85 if node == nodeHovered else 1))


        

    def print(self):

        print("\n\n=====================\nC++ AUTO-GENERATED CODE\n")

        string = "addEdge({}, {});"

        # print addEdge for names
        specialEdges = []
        for edge in self.edges:
            if edge.special:
                specialEdges.append(edge)
            else:
                print(string.format(edge.node1.name().upper(), edge.node2.name().upper()))

        print("\nif (isSkills) {")
        for edge in specialEdges:
            print("\t" + string.format(edge.node1.name().upper(), edge.node2.name().upper()))
        print("}")

        print("\n\n=====================\n")

        # print constants
        nodes = sorted(self.nodes, key = lambda node : int(node.id()))
        print("enum Arm {")
        for node in nodes:
            print("\t{} = {},".format(node.name().upper(), node.id()))
        print("};")

        print("\n\n=====================\n")

        # print values
        print("double angles[NUM_NODES][2] = {")
        for node in nodes:
            text = node.getText()
            t = text.split(" ")
            if len(t) == 2 and "," not in text:
                text = t[0] + ", " + t[1]
            print("\t{" + text + "},")
        print("};")

    def generateSave(self):

        JSON = {}
        JSON["nodes"] = []
        JSON["edges"] = []
        
        i = 0
        for node in self.nodes:
            JSON["nodes"].append(node.save(i))
            i += 1

        for edge in self.edges:
            JSON["edges"].append(edge.save())

        savetext = json.dumps(JSON)

        print("\n\n=====================\nSAVEFILE:\n")
        print(savetext)

        fname = "node_save{}.txt"
        i = 1
        while exists(fname.format(i)):
            i += 1

        if application_path != None:
            fname = join(application_path, fname)
        
        file = open(fname.format(i), "w")
        file.write(savetext)
        file.close()

        


screen = pygame.display.set_mode([WIDTH, HEIGHT], pygame.RESIZABLE)

g = Graph()
if INPUT == "":
    g.add(0, "[Name]", "[theta_1, theta_2]", False, 200, 200)
else:
    for node in info["nodes"]:
       g.add(*node)
    for n1, n2, special in info["edges"]:
        g.addEdge(g.nodes[n1], g.nodes[n2], special)


key = None
nodePressed = None
nodeMoving = None
nodeTyping = None
firstType = True

titleText = fontHuge.render("Z -> new node, Shift+Drag -> new edge, X -> delete, A -> change text, T -> toggle node/edge, S -> generate savefile, P -> print C++ code)", True, WHITE)

while True:

    mx, my = pygame.mouse.get_pos()
    nodeHovered = g.get(mx, my)
    edgeHovered = g.getEdge(mx, my)


    if key == pygame.K_RETURN:
        if nodeTyping:
            nodeTyping.resetText()
            nodeTyping = None

    elif key is not None and nodeTyping is not None:
        char = pygame.key.name(key)
        isID = nodeTyping.highlight == ID_HIGHLIGHT

        def checkFirst():
            global firstType
            if firstType:
                nodeTyping.text[nodeTyping.highlight] = ""
                firstType = False
        
        if char == "space" and not isID:
            checkFirst()
            nodeTyping.text[nodeTyping.highlight] += " "
        elif char == "backspace":
            checkFirst()
            if len(nodeTyping.text[nodeTyping.highlight]) > 0:
                nodeTyping.text[nodeTyping.highlight] = nodeTyping.text[nodeTyping.highlight][:-1]
        elif len(char) == 1 and char in LEGAL and (not isID or char.isnumeric()):
            checkFirst()
            nodeTyping.text[nodeTyping.highlight] +=  "_" if char == "-" else char

        
        
    elif key == pygame.K_z:
        # add
        g.add(g.nextID(), "[Name]", "[theta_1, theta_2]", False, mx, my)
    elif key == pygame.K_t:
        # toggle
        if nodeHovered:
            nodeHovered.special = not nodeHovered.special
        elif edgeHovered:
            edgeHovered.special = not edgeHovered.special
    elif key == pygame.K_a and nodeHovered is not None:
        
        #reset
        if nodeTyping is not None:
            nodeTyping.resetText()

        firstType = True
        
        nodeTyping = nodeHovered
        # change text
        dy = nodeTyping.radius / 6
        if my < nodeTyping.y - dy:
            # change ID
            nodeTyping.highlight = ID_HIGHLIGHT
        elif my > nodeTyping.y + dy:
            # change name
            nodeTyping.highlight = TEXT_HIGHLIGHT
        else:
            nodeTyping.highlight = NAME_HIGHLIGHT

    elif key == pygame.K_p:
        g.print()

    elif key == pygame.K_s:
        # generate savefile
        
        #reset
        if nodeTyping is not None:
            nodeTyping.resetText()
            nodeTyping = None

        g.generateSave()
        

    elif pygame.key.get_pressed()[pygame.K_x] and not nodeTyping:
        g.deleteEdge(edgeHovered)
        g.delete(nodeHovered)


    if nodeMoving is not None:
        nodeMoving.x = mx
        nodeMoving.y = my
    


    screen.fill([40, 40, 40])
    screen.blit(titleText, [20,20])

    if nodePressed is not None:
        drawThickLine(screen, LINE_COLOR, nodePressed.x, nodePressed.y, mx, my, LINE_RADIUS*2)
        drawCircle(screen, LINE_COLOR, [mx,my], 8)
        
    g.draw(screen, mx, my, nodeHovered, edgeHovered, nodeMoving)
    
   

    pygame.display.update()

    key = None
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            key = event.key
        elif event.type == pygame.MOUSEBUTTONDOWN:
            
            if nodeHovered is not None:
                if nodeMoving is None and nodeTyping is None:

                    if shiftPressed():
                        nodePressed = nodeHovered
                    else:
                        nodeMoving = nodeHovered
                else:
                    nodeMoving = None

            if nodeTyping is not None:
                nodeTyping.resetText()
                nodeTyping = None
        elif event.type == pygame.MOUSEBUTTONUP:
            nodeMoving = None
            if nodePressed is not None and nodeHovered is not None and nodePressed != nodeHovered:
                g.addEdge(nodePressed, nodeHovered)
            nodePressed = None

        elif event.type == pygame.VIDEORESIZE:
            # There's some code to add back window content here.
            surface = pygame.display.set_mode((event.w, event.h),
                                              pygame.RESIZABLE)
            WIDTH = event.w
            HEIGHT = event.h
                
        
