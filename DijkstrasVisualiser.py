from PyQt5.QtGui import QColor, QPainter, QPen, QKeyEvent
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QGridLayout, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QLineEdit
import sys
from perlin import perlin, lerp
from math import ceil, floor, sqrt

VERT_SIZE = 7
PAD_Y = 25
PAD_X = 25

GRAPH_WID = 100
GRAPH_HEI = 60

HEIGHT = PAD_Y*2+GRAPH_HEI*VERT_SIZE
WIDTH = PAD_X*2+GRAPH_WID*VERT_SIZE

START_X = round(GRAPH_WID/2)
START_Y = round(GRAPH_HEI/2)
END_X = round(GRAPH_WID*3/4)
END_Y = round(GRAPH_HEI/2)
NOISE = 13

# ------------------------------------------------------------------------------------------------- Graph
class wsggraph(object):
    def __init__(self, x: int = GRAPH_WID, y: int = GRAPH_HEI) -> None:
        self.start_id = 0
        self.end_id = 1
        self.current = self.start_id
        self.g = []
        self.max_id = x*y
        self.row_len = x
        self.diagonal_multiplier = 1.414214
        self.move_directions = [
            1,
            1-self.row_len,
            -self.row_len,
            -self.row_len-1,
            -1,
            self.row_len-1,
            self.row_len,
            self.row_len+1
        ]
        self.set_noise_map()
        self.fill_g()

    def solve(self) -> None:
        while not self.solved():
            self.step()

    def step(self) -> None:
        self.scout()
        self.move()

    def solved(self) -> bool:
        if self.g[self.end_id].explored:
            return(True)
        return(False)

    def move(self) -> None:
        move_to = -1
        for v in self.g:
            if (not v.explored and self.scouted(v.id)) and (move_to == -1 or v.dist < self.g[move_to].dist):
                move_to = v.id
        self.explore(move_to)
        self.current = move_to

    def scouted(self, id: int) -> bool:
        if self.g[id].dist != -1:
            return(True)
        return(False)

    def scout(self) -> None:
        for direction in self.move_directions:
            target = self.current+direction
            if not self.oob(target) and self.valid_direction(self.current, target):
                self.set_total_distance(self.current, target)

    def set_total_distance(self, id: int, target: int) -> None:
        d = self.g[id].dist + self.local_distance(id, target)
        if not self.scouted(target) or d < self.g[target].dist:
            self.g[target].dist = d
            self.g[target].from_id = id

    def local_distance(self, id: int, target: int) -> float:
        self.validate_id(target)
        dist = (self.g[id].stretch + self.g[target].stretch) * self.direction_multiplier(id, target)
        return(dist)

    def direction_multiplier(self, id: int, target: int) -> float:
        diagonal_directions = [
            1-self.row_len,
            -self.row_len-1,
            self.row_len-1,
            self.row_len+1
        ]
        if id - target in diagonal_directions:
            return(self.diagonal_multiplier)
        return(1)

    def valid_direction(self, id: int, target: int) -> bool:
        if self.get_x(id) - self.get_x(target) in [-1, 0, 1]:
            return(True)
        return(False)

    def generate_stretch(self, id: int) -> float:
        x = self.get_x(id)
        y = self.get_y(id)
        noise = self.noise_map.get_noise(x, y)
        if noise > 0:
            noise = sqrt(noise) 
        elif noise < 0:
            noise = -sqrt(abs(noise))
        return(noise/2+0.5)

    def fill_g(self) -> None:
        for id in range(self.max_id):
            v = vert(id, self.generate_stretch(id))
            self.g.append(v)

    def set_noise_map(self, scale: int=NOISE) -> None:
        self.noise_map = perlin(256, 256, scale)

    def set_start(self, x: int, y: int) -> None:
        id = self.get_id(x, y)
        self.explore(id)
        self.start_id = id
        self.current = id
        self.g[id].dist = 0

    def set_end(self, x: int, y: int) -> None:
        id = self.get_id(x, y)
        self.validate_id(id)
        self.end_id = id

    def explore(self, id: int) -> None:
        self.validate_id(id)
        self.g[id].explored = True

    def full_path(self, id: int) -> list:
        full_path_list = []
        full_path_list.append(id)
        while id != self.start_id:
            id = self.g[id].from_id
            full_path_list.append(id)
        return(full_path_list)

    def validate_id(self, id: int) -> None:
        if self.oob(id):
            raise ValueError("id is out of boundaries")

    def oob(self, id: int) -> bool:
        if id in range(self.max_id):
            return(False)
        return(True)

    def get_x(self, id) -> int:
        self.validate_id(id)
        return(id % self.row_len)

    def get_y(self, id) -> int:
        self.validate_id(id)
        return(id // self.row_len)
    
    def get_id(self, x: int, y: int) -> int:
        return(x+y*self.row_len)

class vert(object):    
    def __init__(self,id: int, stretch: float = 0.5) -> None:
        self.id = id
        self.stretch = stretch
        self.explored = False
        self.from_id = -1
        self.dist = -1.
# ------------------------------------------------------------------------------------------------- Graph

# ------------------------------------------------------------------------------------------------- GUI
class main_window(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.is_in_menu = True
        self.init_window()

    def init_window(self) -> None:
        self.setWindowTitle("DijkstrasVisualiser")
        self.show_main_menu()
        self.show()

    def main_menu_connect(self) -> None:
        self.main_menu.to_graph_btn.clicked.connect(self.show_graph)
        self.main_menu.exit_btn.clicked.connect(self.quit_app)

    def graph_btns_connect(self) -> None:
        self.graph_widget.graph_btns.step_btn.clicked.connect(self.step)
        self.graph_widget.graph_btns.solve_btn.clicked.connect(self.solve_path)
        self.graph_widget.graph_btns.to_menu.clicked.connect(self.show_main_menu)
        self.graph_widget.graph_btns.exit_btn.clicked.connect(self.quit_app)

    def step(self) -> None:
        self.graph_widget.graph.step()
        self.graph_widget.update()

    def solve_path(self) -> None:
        self.graph_widget.graph.solve()
        self.graph_widget.update()

    def show_main_menu(self) -> None:
        self.main_menu = main_menu()
        if not self.is_in_menu:
            self.graph_widget.hide()
        self.is_in_menu = True
        self.setCentralWidget(self.main_menu)
        self.main_menu_connect()
        self.main_menu.show()
        self.setFixedSize(640, 480)

    def show_graph(self) -> None:
        wid = int(self.main_menu.l_edit_graph_x.text())
        hei = int(self.main_menu.l_edit_graph_y.text())
        self.graph_widget = graph_widget(wid, hei)
        self.graph_widget.graph.set_start(int(self.main_menu.l_edit_start_x.text()), int(self.main_menu.l_edit_start_y.text()))
        self.graph_widget.graph.set_end(int(self.main_menu.l_edit_end_x.text()), int(self.main_menu.l_edit_end_y.text()))
        self.graph_widget.graph.set_noise_map(int(self.main_menu.l_edit_scale.text()))
        if self.is_in_menu:
            self.main_menu.hide()
        self.is_in_menu = False
        self.setCentralWidget(self.graph_widget)
        self.graph_btns_connect()
        self.graph_widget.show()
        self.setFixedSize(PAD_X*2+VERT_SIZE*wid, PAD_Y*2+VERT_SIZE*hei+60)

    def quit_app(self):
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.close()
    
class main_menu(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.param_widget = QWidget()
        self.param_layout = QGridLayout()
        self.action_widget = QWidget()
        self.action_layout = QGridLayout()
        self.init_window()

    def init_window(self) -> None:
        self.setFixedSize(640, 480)
        self.setLayout(self.main_layout)
        self.set_param()
        self.set_action()

    def set_param(self) -> None:
        self.label_start = menu_label("Start point coordinates:", self.param_widget)
        self.label_end = menu_label("End point coordinates:", self.param_widget)
        self.label_graph = menu_label("Graph dimensions:", self.param_widget)
        self.label_scale = menu_label("Noise scale:", self.param_widget)

        self.label_xs = menu_label("X:", self.param_widget)
        self.l_edit_start_x = short_line_edit(self.param_widget)
        self.label_ys = menu_label("Y:", self.param_widget)
        self.l_edit_start_y = short_line_edit(self.param_widget)

        self.label_xe = menu_label("X:", self.param_widget)
        self.l_edit_end_x = short_line_edit(self.param_widget)
        self.label_ye = menu_label("Y:", self.param_widget)
        self.l_edit_end_y = short_line_edit(self.param_widget)

        self.label_xg = menu_label("X:", self.param_widget)
        self.l_edit_graph_x = short_line_edit(self.param_widget)
        self.label_yg = menu_label("Y:", self.param_widget)
        self.l_edit_graph_y = short_line_edit(self.param_widget)

        self.l_edit_scale = menu_line_edit(self.param_widget)
        self.l_edit_scale.setAlignment(Qt.AlignRight)

        self.param_layout.addWidget(self.label_start, 0, 0, 1, 1)
        self.param_layout.addWidget(self.label_xs, 0, 1, 1, 1)
        self.param_layout.addWidget(self.l_edit_start_x, 0, 2, 1, 1)
        self.param_layout.addWidget(self.label_ys, 0, 3, 1, 1)
        self.param_layout.addWidget(self.l_edit_start_y, 0, 4, 1, 1)

        self.param_layout.addWidget(self.label_end, 1, 0, 1, 1)
        self.param_layout.addWidget(self.label_xe, 1, 1, 1, 1)
        self.param_layout.addWidget(self.l_edit_end_x, 1, 2, 1, 1)
        self.param_layout.addWidget(self.label_ye, 1, 3, 1, 1)
        self.param_layout.addWidget(self.l_edit_end_y, 1, 4, 1, 1)

        self.param_layout.addWidget(self.label_graph, 2, 0, 1, 1)
        self.param_layout.addWidget(self.label_xg, 2, 1, 1, 1)
        self.param_layout.addWidget(self.l_edit_graph_x, 2, 2, 1, 1)
        self.param_layout.addWidget(self.label_yg, 2, 3, 1, 1)
        self.param_layout.addWidget(self.l_edit_graph_y, 2, 4, 1, 1)

        self.param_layout.addWidget(self.label_scale, 3, 0, 1, 1)
        self.param_layout.addWidget(self.l_edit_scale, 3, 2, 1, 3)

        self.reset_entry()
        self.param_widget.setLayout(self.param_layout)
        self.main_layout.addWidget(self.param_widget)

    def set_action(self) -> None:
        self.to_graph_btn = menu_btn("Graph", self.action_widget)
        self.action_layout.addWidget(self.to_graph_btn, 0, 0)

        self.exit_btn = menu_btn("Exit", self.action_widget)
        self.action_layout.addWidget(self.exit_btn, 0, 2)

        self.reset_btn = menu_btn("Reset", self.action_widget)
        self.action_layout.addWidget(self.reset_btn, 0, 1)
        self.reset_btn.clicked.connect(self.reset_entry)

        self.action_widget.setLayout(self.action_layout)
        self.main_layout.addWidget(self.action_widget)

    def reset_entry(self):
        self.l_edit_start_x.setText(str(START_X))
        self.l_edit_start_y.setText(str(START_Y))
        self.l_edit_end_x.setText(str(END_X))
        self.l_edit_end_y.setText(str(END_Y))
        self.l_edit_graph_x.setText(str(GRAPH_WID))
        self.l_edit_graph_y.setText(str(GRAPH_HEI))
        self.l_edit_scale.setText(str(NOISE))

class menu_label(QLabel):
    def __init__(self, text="", parent=None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignRight)

class menu_line_edit(QLineEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignRight)
        self.setFixedSize(100, 40)
        self.setInputMask("999")

class short_line_edit(menu_line_edit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignLeft)
        self.setFixedSize(100,40)

class menu_btn(QPushButton):
    def __init__(self, text=None, parent=None) -> None:
        super().__init__(text, parent)
        self.setFixedSize(100,40)

class GraphBtn(menu_btn): 
    def __init__(self, text=None, parent=None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignBottom)

class GraphBtns(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.step_btn = menu_btn("1 step", self)
        self.solve_btn = menu_btn("Solve", self)
        self.to_menu = menu_btn("Menu", self)
        self.exit_btn = menu_btn("Exit", self)
        self.btn_layout = QGridLayout()

        self.btn_layout.addWidget(self.step_btn, 0, 0)
        self.btn_layout.addWidget(self.solve_btn, 0, 1)
        self.btn_layout.addWidget(self.to_menu, 0, 2)
        self.btn_layout.addWidget(self.exit_btn, 0, 3)
        self.setLayout(self.btn_layout)

class graph_widget(QWidget):
    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.gx = x
        self.gy = y
        self.graph = wsggraph(x, y)
        self.graph_placeholder = QWidget()
        self.graph_btns = GraphBtns()
        self.graph_layout = QVBoxLayout()
        self.init_widget()

    def init_widget(self) -> None:
        self.graph_placeholder.setFixedSize(WIDTH, HEIGHT)
        self.setFixedSize(self.gx*VERT_SIZE+PAD_X*2, self.gy*VERT_SIZE+PAD_Y*2+50)
        self.graph_layout.addWidget(self.graph_placeholder, alignment=Qt.AlignTop)
        self.graph_layout.addWidget(self.graph_btns, alignment=Qt.AlignBottom)
        self.setLayout(self.graph_layout)
    
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        self.paint_graph(painter)

    def paint_vert(self, painter: object, color: object, y: int, x: int) -> None:
        painter.setPen(QPen(color, 1, Qt.SolidLine))
        painter.setBrush(color)
        painter.drawRect(y, x, VERT_SIZE, VERT_SIZE)

    def base_color(self, n: float) -> QColor:
        if n>1 or n<0:
            raise ValueError("not 0<=n<=1")
        n=1-n
        n255 = round(n*200)
        return(QColor(n255, n255, n255))

    def explored_color(self, n: float) -> QColor:
        if n>1 or n<0:
            raise ValueError("not 0<=n<=1")
        n=1-n
        n255 = round(n*200)
        return(QColor(n255, n255+50, n255))

    def paint_graph(self, painter: object) -> None:
        color_start = QColor(25,220,25)
        color_end = QColor(25,25,220)
        color_path = QColor(255,255,255)
        path = []
        if self.graph.solved():
            path = self.graph.full_path(self.graph.end_id)
        for v in self.graph.g:
            y = self.graph.get_y(v.id)*VERT_SIZE+PAD_Y
            x = self.graph.get_x(v.id)*VERT_SIZE+PAD_X
            self.paint_vert(painter, self.base_color(v.stretch), x, y)
            if v.explored:
                self.paint_vert(painter, self.explored_color(v.stretch), x, y)
            if v.id == self.graph.current:
                self.paint_vert(painter, color_path, x, y)
            if v.id in path:
                self.paint_vert(painter, color_path, x, y)
            if v.id == self.graph.start_id:
                self.paint_vert(painter, color_start, x, y)
            if v.id == self.graph.end_id:
                self.paint_vert(painter, color_end, x, y)




app = QApplication(sys.argv) # Start.
window = main_window()
sys.exit(app.exec()) # End.