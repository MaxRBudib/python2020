from mesa import Agent, Model
from mesa.space import Grid
from mesa.time import RandomActivation
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.datacollection import DataCollector
from mesa.visualization.modules import ChartModule
import random

class Tree(Agent):
    FINE = 0
    BURNING = 1
    BURNED_OUT = 2
    def __init__(self, model: Model, pos, probability, south, west, jumps):
        super().__init__(model.next_id(), model)
        self.condition = self.FINE
        self.probability = probability
        self.pos = pos
        self.jumps = jumps
        self.south = south
        self.west = west
        self.chance = random.randint(1, 100) 

    def step(self):
        neigh = self.model.grid.neighbor_iter(self.pos, moore=False)
        #print(neigh)
        arr = []
        if self.condition == self.BURNING:
            for i in neigh:
                if self.south == 0:
                    if i.pos[1] > self.pos[1] or i.pos[1] < self.pos[1]:
                        if i.condition == self.FINE and self.chance <= self.probability + self.south:
                                i.condition = self.BURNING
                if self.west == 0:
                    if i.pos[0] > self.pos[0] or i.pos[0] < self.pos[0]:
                        if i.condition == self.FINE and self.chance <= self.probability + self.south:
                                i.condition = self.BURNING
                if self.south > 0:    
                    if i.pos[1] > self.pos[1]:
                        if i.condition == self.FINE and self.chance <= self.probability + self.south:
                            i.condition = self.BURNING
                else:
                    if i.pos[1] < self.pos[1]:
                        if i.condition == self.FINE and self.chance <= self.probability - self.south:
                            i.condition = self.BURNING
                if self.west > 0:    
                    if i.pos[0] > self.pos[0]:
                        if i.condition == self.FINE and self.chance <= self.probability + self.west:
                            i.condition = self.BURNING
                else:
                    if i.pos[0] < self.pos[0]:
                        if i.condition == self.FINE and self.chance <= self.probability - self.west:
                            i.condition = self.BURNING
                if self.jumps:
                    if self.west >= 0:
                        if i.pos[0] + round(self.west/8) > 49 or i.pos[1] + round(self.south/8) > 49 or i.pos[0] + round(self.west/8) < 0 or i.pos[1] + round(self.south/8) < 0:
                            self.jumps = False
                        else:
                            see = self.model.grid.get_cell_list_contents([(i.pos[0] + round(self.west/8), i.pos[1] + round(self.south/8))])
                            if len(see) > 0:
                                if see[0].condition == self.FINE and self.chance <= self.probability:
                                   see[0].condition = self.BURNING 
            self.condition = self.BURNED_OUT

class Forest(Model):
    def __init__(self, probability_of_spread, south_wind_speed, west_wind_speed, big_jumps, height=50, width=50, density=0.45):
        super().__init__()
        self.schedule = RandomActivation(self)
        self.rand = probability_of_spread
        self.swind = south_wind_speed
        self.wwind = west_wind_speed
        self.jumps = big_jumps
        self.grid = Grid(height, width, torus=False)
        for _,x,y in self.grid.coord_iter():
            if self.random.random() < density:
                tree = Tree(self, (x,y), self.rand, self.swind, self.wwind, self.jumps)
                if x == 0:
                    tree.condition = Tree.BURNING
                self.grid.place_agent(tree, tree.pos)
                self.schedule.add(tree)

        self.datacollector = DataCollector({"Percent burned": lambda m: self.count_type(m, Tree.BURNED_OUT) / len(self.schedule.agents)})
        
    @staticmethod
    def count_type(model, condition):
        count = 0
        for tree in model.schedule.agents:
            if tree.condition == condition:
                count += 1
        return count   

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)
        if self.count_type(self, Tree.BURNING) == 0:
            self.running = False

def agent_portrayal(agent):
    if agent.condition == Tree.FINE:
        portrayal = {"Shape": "circle", "Filled": "true", "Color": "Green", "r": 0.75, "Layer": 0}
    elif agent.condition == Tree.BURNING:
        portrayal = {"Shape": "circle", "Filled": "true", "Color": "Red", "r": 0.75, "Layer": 0}
    elif agent.condition == Tree.BURNED_OUT:
        portrayal = {"Shape": "circle", "Filled": "true", "Color": "Gray", "r": 0.75, "Layer": 0}
    else:
        portrayal = {}

    return portrayal

grid = CanvasGrid(agent_portrayal, 50, 50, 450, 450)

chart = ChartModule([{"Label": "Percent burned", "Color": "Black"}], data_collector_name='datacollector')

server = ModularServer(Forest,
                       [grid, chart],
                       "Forest",
                       {"density": UserSettableParameter("slider", "Tree density", 0.45, 0.01, 1.0, 0.01),
                       "probability_of_spread": UserSettableParameter("slider", "Probability", 50, 0, 100, 1),
                       "south_wind_speed": UserSettableParameter("slider", "South Wind Speed", 0, -25, 25, 1),
                       "west_wind_speed": UserSettableParameter("slider", "West Wind Speed", 0, -25, 25, 1),
                       "big_jumps": UserSettableParameter("checkbox", "My_boolean", True)})

server.port = 8522 
server.launch()