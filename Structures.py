import numpy as np
import matplotlib.pyplot as plt
import random as rnd
from PriorityQueue import PriorityQueue



class Passenger:

    '''A Passenger object represents an user of the metro network. It is described by the shape of its destination and the route that it is planning to use. The route is given by a pile of tuples (line number, goal). '''

    def __init__(self, shape, route=[]):
        self.shape = shape
        self.route = route
    
    def computeRoute(self, station, network):
        G = network.graph
        start = station.idt
        goal = self.shape
        n = len(network.stations)
        p = len(network.lines)
        spanningforest = [None for _ in range(n * p)]
        deja_vu = [False for _ in range(n * p)]
        U = PriorityQueue(len(G) * len(G[0]))

        for i in range(p):
            U.push(start + n * i, - float('inf'))
            deja_vu[start + n * i] = True
        
        while U.length() != 0:
            (u, k) = U.pop()
            if deja_vu[u]:
                continue
            elif network.stations[u % n].shape == goal:
                goal = u
            else:
                deja_vu[u] = True
                for (v, w) in G[u]:
                    if - U.priority(v) > - k + w:
                        U.changePrio(v, - k + w)
                        spanningforest[v] = u
        
        route = []
        while goal != None:
            route.append((goal // n, goal % n))
            goal = spanningforest[goal]

        self.route = route

        






class Station:

    '''A Station object represents a metro station. It is defined by its id, its shape, its capacity, its spawn rate of passengers, the lines that go through this station and the passengers currently waiting at the station. sp gives the different rates of spawning of shapes. The variable time increases 1 at a time to spTime and then returns to 0, and a random passenger is created then. If there are more passengers waiting than the capacity allowed, the variable overloadtime increases, and decreases to 0 otherwise.'''

    def __init__(self, idt, shape, waiting, lines, spRate, loc=None, spTime=100, capacity=8):
        self.idt = idt
        self.loc = loc
        self.shape = shape
        self.waiting = waiting
        self.time = 0
        self.spRate = spRate
        self.spTime = spTime
        self.capacity = capacity
        self.overloadTime = 0
        self.lines = lines
        self.transported = 0
    
    def upCrowded(self, network):
        if self.overloadTime >= 100:
            network.end = True
        elif self.capacity < len(self.waiting):
            self.overloadTime += 1
        elif self.overloadTime > 0:
            self.overloadTime -= 1
    
    def count(self):
        self.transported += 1
    
    def spawn(self, network):
        if self.time == self.spTime:
            r = rnd.random()
            for (shape, ratio) in self.spRate:
                if r < ratio:
                    passenger = Passenger(shape)
                    passenger.computeRoute(self, network)
                    self.waiting.append(passenger)
                    break
                elif r >= ratio:
                    r -= ratio
            self.time = 0
        else:
            self.time += 1



class Network:

    '''A Map object is a graph representing a metro network. It is given by the list of its vertex, that are the stations, an array of the times it costs to travel between any pair of stations (integer) and the metro lines currently working.'''

    def __init__(self, stations, distances, lines):
        self.stations = stations
        self.distances = distances
        self.lines = lines
        self.end = False
        self.graph = self.createGraph()

    def nextState(self):
        for station in self.stations:
            station.spawn(self)
            station.upCrowded(self)
        for line in self.lines:
            line.nextState(self.distances, self.stations)
    
    def oneEternityLater(self, n):
        while n > 0 and not self.end:
            self.nextState()
            n -= 1
        
        return self.end
    
    def createGraph(self):
        G = [[] for _ in self.lines for _ in self.stations]

        for line in self.lines:
            n = len(self.stations)
            for k in range(len(line.route)):
                s = self.stations[line.route[k]]
                d = 0
                for l in range(1, len(line.route)):
                    t = self.stations[line.route[(k + l) % len(line.route)]]
                    d += self.distances[s.idt][t.idt]
                    G[s.idt + n * line.nb].append((t.idt + n * line.nb, d))
        
        for s in self.stations:
            for line1 in s.lines:
                for line2 in s.lines:
                    if line1 != line2:
                        G[s.idt + n * line1].append(s.idt + n * line2, self.lines[line2].waitingTime(self))

        return G
    
    def plot(self):

        shapeList = ["s", "^", "o", "p", "P", "*", "d"]

        for line in self.lines:
            X = [self.stations[i].loc[0] for i in line.route]
            Y = [self.stations[i].loc[1] for i in line.route]
            X.append(X[0])
            Y.append(Y[0])
            plt.plot(X, Y, linewidth=2)
        
        for station in self.stations:
            (x,y) = station.loc
            plt.scatter(x, y, s=64, c='black', marker=shapeList[station.shape])
        
        plt.axis('equal')
        plt.show()







class Line:

    '''A Line object represents a metro line. It is defined by an unique number, the list of stations on this line (which is ALWAYS CYCLIC) and the list of trains on this line. '''

    def __init__(self, nb, route, trains):
        self.nb = nb
        self.route = route
        self.trains = trains
    
    def nextState(self, dist, stations):
        for train in self.trains:
            if train.nextTime != 0:
                train.nextTime -= 1
            else:
                station = stations[self.route[train.nextDest]]
                train.nextDest = (train.nextDest + 1) % len(self.route)
                nextStation = stations[self.route[train.nextDest]]
                train.nextTime = dist[station.idt][nextStation.idt]
                train.empty(station)
                train.fill(station)
    
    def waitingTime(self, network):
        return sum([network.distances[self.route[k]][self.route[(k + 1) % len(self.route)]] for k in range(len(self.route))]) / (2 * len(self.trains))





class Train:

    '''A Train object represents a metro train. It is defined by the number of the line it is working on, its next destination, the time needed to go to the next destination, the list of passengers onboard and its capacity.'''

    def __init__(self, line, nextDest, nextTime, passengers, capacity):
        self.line = line
        self.nextDest = nextDest
        self.nextTime = nextTime
        self.passengers = passengers
        self.capacity = capacity
    
    def empty(self, station):
        i = 0
        stillGoing = []
        while i < len(self.passengers):
            passenger = self.passengers[i]
            if passenger.shape == station.shape:
                station.count()
            elif passenger.route[-1][1] == station.idt:
                passenger.route.pop()
                station.waiting.append(passenger)
            else:
                stillGoing.append(passenger)
            i += 1
        self.passengers = stillGoing
    
    def fill(self, station):
        i = 0
        stillWaiting = []
        while i < len(station.waiting) and self.capacity > len(self.passengers):
            passenger = station.waiting[i]
            if passenger.route[-1][0] == self.line:
                self.passengers.append(passenger)
            else:
                stillWaiting.append(passenger)
            i += 1
        station.waiting = stillWaiting


    