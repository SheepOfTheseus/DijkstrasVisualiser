from math import pi, cos, sin, floor
from random import random

def lerp(a: float, b: float, t: float) -> float:
    return(a+(b-a)*t)

def smoothstep(t: float) -> float:
    return(t*t*(3-2*t))    

def dot(a: object, b: object) -> float:
    return(a.x*b.x+a.y*b.y)

def unit_vector() -> object:
    phi = 2*pi*random()
    return(vec(cos(phi),sin(phi)))

class vec():
    def __init__(self, x:float, y: float) -> None:
        self.x = x
        self.y = y

class perlin():
    def __init__(self, wid: int, hei: int, scale: float) -> None:
        self.wid = wid
        self.hei = hei
        self.scale = scale
        self.values = []
        self.refill()

    def get_noise(self, x: float,y: float) -> float:
        x /= self.scale
        y /= self.scale

        floored = vec(floor(x),floor(y))

        v1 = self.get_value(floored.x,floored.y)       
        v2 = self.get_value(floored.x+1,floored.y)
        v3 = self.get_value(floored.x,floored.y+1)
        v4 = self.get_value(floored.x+1,floored.y+1)       

        local = vec(x-floored.x, y-floored.y)

        p1 = vec(local.x, local.y)
        p2 = vec(local.x-1, local.y)
        p3 = vec(local.x, local.y-1)
        p4 = vec(local.x-1, local.y-1)

        d1 = dot(v1, p1)
        d2 = dot(v2, p2)
        d3 = dot(v3, p3)
        d4 = dot(v4, p4)

        ix1 = lerp(d1, d2, smoothstep(local.x))
        ix2 = lerp(d3, d4, smoothstep(local.x))

        return(lerp(ix1, ix2, smoothstep(local.y)))


    #def construct(self) -> None:
    #    pass

    def refill(self) -> None:
        self.values = []
        for i in range(self.wid*self.hei):
            self.values.append(unit_vector())

    def get_index(self, x: int, y: int) -> int:
        if x in range(self.wid) and y in range(self.hei):
            return(y*self.wid+x)
        raise ValueError("point is oob")

    def get_value(self, x: int, y: int) -> float:
        return(self.values[self.get_index(x,y)])
