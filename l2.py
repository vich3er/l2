import tkinter as tk
from tkinter import ttk
from collections import deque
import time
import math

class GraphSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Пошук у ширину (BFS) та глибину (DFS) на графах")
        self.root.geometry("1340x860")

        self.nodes = {}        
        self.edges = set()     
        self.saved_cross_edges = set() 
        self.selected_graph_type = tk.StringVar(value="undirected") 
        self.active_graph_type = "undirected"                       
        self.order_strategy = tk.StringVar(value="asc")             
        self.algorithm_var = tk.StringVar(value="BFS")
        
        self.is_running = False
        self.is_paused = False
        self.after_id = None

        self.steps_history = []
        self.current_step_idx = 0
        self.search_result = None

        self._init_default_graph()
        self._build_ui()
        self.redraw_graph()

    def _init_default_graph(self):
        self.nodes = {
            1: (600, 45),
            2: (340, 130), 7: (220, 220), 8: (320, 220), 17: (160, 310), 18: (240, 310),
            3: (470, 130), 9: (410, 230), 10: (480, 230), 19: (380, 330), 20: (450, 330),
            4: (600, 140), 11: (560, 250), 12: (640, 250), 21: (540, 360), 22: (640, 360),
            5: (730, 130), 13: (720, 230), 14: (790, 230), 23: (720, 330), 24: (800, 330),
            6: (860, 130), 15: (870, 220), 16: (970, 220), 25: (930, 310), 26: (1030, 310),
            27: (200, 430), 28: (420, 450), 29: (600, 470), 30: (760, 450), 31: (970, 430),
            32: (600, 560)
        }

        initial_edges = [
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
            (2, 7), (2, 8), (7, 17), (7, 18), (17, 27),
            (3, 9), (3, 10), (9, 19), (10, 20), (19, 28),
            (4, 11), (4, 12), (11, 21), (12, 22), (21, 29),
            (5, 13), (5, 14), (13, 23), (14, 24), (24, 30),
            (6, 15), (6, 16), (16, 25), (16, 26), (26, 31),
            (27, 28), (28, 32), (29, 32), (30, 32), (31, 30),
            (8, 9), (10, 11), (12, 13), (14, 15), (18, 19), (22, 23)
        ]
        self.edges = set(initial_edges)
        self.saved_cross_edges = {
            (8, 9), (10, 11), (12, 13), (14, 15), (18, 19), (22, 23),
            (27, 28), (31, 30), (28, 32), (30, 32)
        }
        self.active_graph_type = "undirected"
        self.selected_graph_type.set("undirected")

    def _build_ui(self):
        control_panel = ttk.Frame(self.root, padding=6)
        control_panel.pack(side=tk.LEFT, fill=tk.Y)

        canvas_frame = ttk.Frame(self.root, padding=2)
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#F8FAFC")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        alg_group = ttk.LabelFrame(control_panel, text="Алгоритм пошуку", padding=4)
        alg_group.pack(fill=tk.X, pady=2)
        ttk.Radiobutton(alg_group, text="В ширину (BFS)", value="BFS",
                        variable=self.algorithm_var, command=self._on_search_param_change).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(alg_group, text="В глибину (DFS)", value="DFS",
                        variable=self.algorithm_var, command=self._on_search_param_change).pack(side=tk.LEFT)

        type_group = ttk.LabelFrame(control_panel, text="Вид графа", padding=4)
        type_group.pack(fill=tk.X, pady=2)
        ttk.Radiobutton(type_group, text="Звичайний (Неорієнтований)", value="undirected",
                        variable=self.selected_graph_type).pack(anchor=tk.W)
        ttk.Radiobutton(type_group, text="Орієнтований (Орграф зі стрілками)", value="directed",
                        variable=self.selected_graph_type).pack(anchor=tk.W)
        ttk.Radiobutton(type_group, text="Дерево (Без циклів)", value="tree",
                        variable=self.selected_graph_type).pack(anchor=tk.W)

        self.btn_save_type = ttk.Button(type_group, text="Застосувати вид графа",
                                        command=self.apply_graph_type)
        self.btn_save_type.pack(fill=tk.X, pady=(4, 2))

        search_group = ttk.LabelFrame(control_panel, text="Параметри пошуку", padding=4)
        search_group.pack(fill=tk.X, pady=2)

        f_nodes = ttk.Frame(search_group)
        f_nodes.pack(fill=tk.X, pady=2)
        ttk.Label(f_nodes, text="Старт:").grid(row=0, column=0, sticky=tk.W)
        self.start_combo = ttk.Combobox(f_nodes, width=5, state="readonly")
        self.start_combo.grid(row=0, column=1, padx=2)
        self.start_combo.bind("<<ComboboxSelected>>", self.on_start_goal_changed)

        ttk.Label(f_nodes, text="Мета:").grid(row=0, column=2, padx=(4, 0))
        self.goal_combo = ttk.Combobox(f_nodes, width=5, state="readonly")
        self.goal_combo.grid(row=0, column=3, padx=2)
        self.goal_combo.bind("<<ComboboxSelected>>", self.on_start_goal_changed)

        ttk.Button(search_group, text="⇄ Дзеркальна зміна (Старт ↔ Мета)",
                   command=self.swap_start_goal).pack(fill=tk.X, pady=2)

        ttk.Label(search_group, text="Порядок обходу суміжних вершин:").pack(anchor=tk.W, pady=(2, 0))
        f_ord = ttk.Frame(search_group)
        f_ord.pack(fill=tk.X, pady=1)
        ttk.Radiobutton(f_ord, text="За зростанням (1➔N)", value="asc", 
                        variable=self.order_strategy, command=self._on_search_param_change).pack(side=tk.LEFT)
        ttk.Radiobutton(f_ord, text="За спаданням (N➔1)", value="desc", 
                        variable=self.order_strategy, command=self._on_search_param_change).pack(side=tk.LEFT, padx=6)

        f_speed = ttk.Frame(search_group)
        f_speed.pack(fill=tk.X, pady=2)
        ttk.Label(f_speed, text="Затримка (мс):").pack(side=tk.LEFT)
        self.speed_scale = ttk.Scale(f_speed, from_=20, to=800, value=150, orient=tk.HORIZONTAL)
        self.speed_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=4)

        f_action_btns = ttk.Frame(search_group)
        f_action_btns.pack(fill=tk.X, pady=3)
        self.btn_run = ttk.Button(f_action_btns, text="▶ Запустити пошук", command=self.on_run_clicked)
        self.btn_run.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        self.btn_pause = ttk.Button(f_action_btns, text="⏸ Пауза", command=self.pause_search, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        self.btn_reset_search = ttk.Button(search_group, text="⏹ Скинути пошук", command=self.reset_search_state)
        self.btn_reset_search.pack(fill=tk.X, pady=2)

        edit_group = ttk.LabelFrame(control_panel, text="Редагування графа (|V| та |E|)", padding=4)
        edit_group.pack(fill=tk.X, pady=2)

        ttk.Label(edit_group, text="Вершини (|V|):", font=("Arial", 8, "bold")).pack(anchor=tk.W)
        f_v = ttk.Frame(edit_group)
        f_v.pack(fill=tk.X, pady=1)
        ttk.Label(f_v, text="ID:").grid(row=0, column=0, sticky=tk.W)
        self.entry_v_new = ttk.Entry(f_v, width=4)
        self.entry_v_new.grid(row=0, column=1, padx=2)

        ttk.Label(f_v, text="Сусід:").grid(row=0, column=2, padx=(2, 0))
        self.entry_v_parent = ttk.Entry(f_v, width=4)
        self.entry_v_parent.grid(row=0, column=3, padx=2)

        f_v_btn = ttk.Frame(edit_group)
        f_v_btn.pack(fill=tk.X, pady=1)
        ttk.Button(f_v_btn, text="+ Додати", command=self.add_connected_vertex).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        ttk.Button(f_v_btn, text="- Видалити", command=self.remove_vertex).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=1)

        ttk.Separator(edit_group, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)

        ttk.Label(edit_group, text="Ребра / Дуги (|E|):", font=("Arial", 8, "bold")).pack(anchor=tk.W)
        f_e = ttk.Frame(edit_group)
        f_e.pack(fill=tk.X, pady=1)
        ttk.Label(f_e, text="З:").pack(side=tk.LEFT)
        self.entry_u = ttk.Entry(f_e, width=4)
        self.entry_u.pack(side=tk.LEFT, padx=2)
        ttk.Label(f_e, text="До:").pack(side=tk.LEFT)
        self.entry_v = ttk.Entry(f_e, width=4)
        self.entry_v.pack(side=tk.LEFT, padx=2)

        self.reverse_edge_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(edit_group, text="Зворотний напрямок (До ➔ З)",
                        variable=self.reverse_edge_var).pack(anchor=tk.W)

        f_e_btn = ttk.Frame(edit_group)
        f_e_btn.pack(fill=tk.X, pady=1)
        ttk.Button(f_e_btn, text="+ Зв'язок", command=self.add_edge).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        ttk.Button(f_e_btn, text="- Зв'язок", command=self.remove_edge).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=1)

        ttk.Button(control_panel, text="Початковий граф (Скинути)", command=self.reset_to_default).pack(fill=tk.X, pady=3)

        self.status_label = tk.Label(control_panel, text="Готово до роботи", fg="#2563EB",
                                     font=("Arial", 8, "italic"), wraplength=260, justify=tk.LEFT)
        self.status_label.pack(fill=tk.X, pady=2)

        legend_frame = ttk.LabelFrame(control_panel, text="Позначення кольорів", padding=3)
        legend_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=2)

        legend_items = [
            ("Не відвідано", "#E2E8F0"),
            ("В черзі/стеку", "#FDBA74"),
            ("Розкрито", "#86EFAC"),
            ("Знайдений шлях", "#3B82F6"),
            ("Старт / Мета", "#FCA5A5")
        ]

        for i, (text, color) in enumerate(legend_items):
            row = i // 2
            col = (i % 2) * 2
            tk.Label(legend_frame, bg=color, width=2, height=1, relief="solid", bd=1).grid(row=row, column=col, padx=2, pady=1, sticky=tk.W)
            ttk.Label(legend_frame, text=text, font=("Arial", 8)).grid(row=row, column=col + 1, padx=(0, 4), pady=1, sticky=tk.W)

        self._refresh_combos()

    def _on_search_param_change(self):
        if self.is_paused or self.steps_history:
            self.reset_search_state()

    def on_start_goal_changed(self, event=None):
        self.reset_search_state()
        self.set_status(f"Обрано: Старт={self.start_combo.get()}, Мета={self.goal_combo.get()}")
        self.redraw_graph()

    def set_status(self, text, color="#1E293B"):
        self.status_label.config(text=text, fg=color)

    def _refresh_combos(self):
        sorted_keys = sorted(self.nodes.keys())
        self.start_combo['values'] = sorted_keys
        self.goal_combo['values'] = sorted_keys
        if sorted_keys:
            if not self.start_combo.get() or int(self.start_combo.get()) not in self.nodes:
                self.start_combo.set(sorted_keys[0])
            if not self.goal_combo.get() or int(self.goal_combo.get()) not in self.nodes:
                self.goal_combo.set(32 if 32 in self.nodes else sorted_keys[-1])

    def swap_start_goal(self):
        self.reset_search_state()
        s, g = self.start_combo.get(), self.goal_combo.get()
        self.start_combo.set(g)
        self.goal_combo.set(s)
        self.set_status("Старт і мету поміняно місцями.")
        self.redraw_graph()

    def apply_graph_type(self):
        self.reset_search_state()
        self.active_graph_type = self.selected_graph_type.get()

        if self.active_graph_type == "tree":
            self.edges = {e for e in self.edges if e not in self.saved_cross_edges and (e[1], e[0]) not in self.saved_cross_edges}
            self.set_status("Застосовано: Дерево (поперечні зв'язки приховано).", "#16A34A")
        else:
            for u, v in self.saved_cross_edges:
                if u in self.nodes and v in self.nodes:
                    self.edges.add((u, v))
            name = "Орграф" if self.active_graph_type == "directed" else "Ззвичайний граф"
            self.set_status(f"Застосовано: {name}.", "#16A34A")

        self.redraw_graph()

    def reset_to_default(self):
        self.reset_search_state()
        self._init_default_graph()
        self._refresh_combos()
        self.redraw_graph()
        self.set_status("Граф скинуто: |V|=32, |E|=41.", "#16A34A")

    def get_adj_list(self):
        adj = {v: [] for v in self.nodes}
        for u, v in self.edges:
            if u in adj and v in adj:
                adj[u].append(v)
                if self.active_graph_type in ("undirected", "tree"):
                    adj[v].append(u)

        reverse_flag = (self.order_strategy.get() == "desc")
        for v in adj:
            adj[v].sort(reverse=reverse_flag)
        return adj

    def redraw_graph(self, highlighted_nodes=None, path_edges=None):
        if highlighted_nodes is None:
            highlighted_nodes = {}
        if path_edges is None:
            path_edges = set()

        self.canvas.delete("all")
        show_arrow = (self.active_graph_type == "directed")
        node_r = 14

        for u, v in self.edges:
            if u not in self.nodes or v not in self.nodes:
                continue
            x1, y1 = self.nodes[u]
            x2, y2 = self.nodes[v]

            dx = x2 - x1
            dy = y2 - y1
            dist = math.hypot(dx, dy)

            if dist > 0:
                end_x = x2 - (dx / dist) * node_r
                end_y = y2 - (dy / dist) * node_r
                start_x = x1 + (dx / dist) * node_r if show_arrow else x1
                start_y = y1 + (dy / dist) * node_r if show_arrow else y1
            else:
                start_x, start_y, end_x, end_y = x1, y1, x2, y2

            is_path = (u, v) in path_edges or (self.active_graph_type in ("undirected", "tree") and (v, u) in path_edges)
            color = "#2563EB" if is_path else "#94A3B8"
            width = 3.2 if is_path else 1.5

            arrow_opt = tk.LAST if show_arrow else None
            self.canvas.create_line(start_x, start_y, end_x, end_y, fill=color, width=width,
                                    arrow=arrow_opt, arrowshape=(11, 13, 5))

        start_v = int(self.start_combo.get()) if self.start_combo.get().isdigit() else None
        goal_v = int(self.goal_combo.get()) if self.goal_combo.get().isdigit() else None

        for node_id, (x, y) in self.nodes.items():
            fill_color = highlighted_nodes.get(node_id, "#E2E8F0")
            outline_color = "#334155"
            outline_width = 1.5

            if node_id in (start_v, goal_v) and node_id not in highlighted_nodes:
                fill_color = "#FECACA"
                outline_color = "#DC2626"
                outline_width = 2.5

            self.canvas.create_oval(x - node_r, y - node_r, x + node_r, y + node_r,
                                    fill=fill_color, outline=outline_color, width=outline_width)
            self.canvas.create_text(x, y, text=str(node_id), font=("Arial", 9, "bold"), fill="#0F172A")

    def add_connected_vertex(self):
        self.reset_search_state()
        try:
            new_id = int(self.entry_v_new.get())
            parent_id = int(self.entry_v_parent.get())

            if new_id in self.nodes:
                self.set_status(f"Помилка: вершина {new_id} вже існує.", "#DC2626")
                return
            if parent_id not in self.nodes:
                self.set_status(f"Помилка: сусіда {parent_id} не існує.", "#DC2626")
                return

            px, py = self.nodes[parent_id]
            existing_count = sum(1 for (u, v) in self.edges if u == parent_id or v == parent_id)
            angle = (existing_count * 0.7) + 0.3
            new_x = int(px + 65 * math.cos(angle))
            new_y = int(py + 65 * math.sin(angle) + 15)

            new_x = max(25, min(1200, new_x))
            new_y = max(25, min(700, new_y))

            self.nodes[new_id] = (new_x, new_y)
            self.edges.add((parent_id, new_id))

            self._refresh_combos()
            self.redraw_graph()
            self.set_status(f"Додано вершину {new_id} до {parent_id}.", "#16A34A")
        except ValueError:
            self.set_status("Введіть цілі числа для ID та сусіда.", "#DC2626")

    def remove_vertex(self):
        self.reset_search_state()
        try:
            v_id = int(self.entry_v_new.get())
            if v_id not in self.nodes:
                self.set_status(f"Вершини {v_id} не існує.", "#DC2626")
                return
            del self.nodes[v_id]
            self.edges = {e for e in self.edges if e[0] != v_id and e[1] != v_id}
            self.saved_cross_edges = {e for e in self.saved_cross_edges if e[0] != v_id and e[1] != v_id}
            self._refresh_combos()
            self.redraw_graph()
            self.set_status(f"Вершину {v_id} видалено.", "#16A34A")
        except ValueError:
            self.set_status("Введіть коректний числовий ID вершини.", "#DC2626")

    def add_edge(self):
        self.reset_search_state()
        try:
            u = int(self.entry_u.get())
            v = int(self.entry_v.get())
            if u not in self.nodes or v not in self.nodes:
                self.set_status("Обидві вершини мають існувати.", "#DC2626")
                return
            if u == v:
                self.set_status("Петлі заборонені.", "#DC2626")
                return

            if self.reverse_edge_var.get():
                self.edges.add((v, u))
                self.set_status(f"Додано: {v} ➔ {u}.", "#16A34A")
            else:
                self.edges.add((u, v))
                self.set_status(f"Додано: {u} ➔ {v}.", "#16A34A")

            self.redraw_graph()
        except ValueError:
            self.set_status("Введіть коректні числа для З і До.", "#DC2626")

    def remove_edge(self):
        self.reset_search_state()
        try:
            u = int(self.entry_u.get())
            v = int(self.entry_v.get())
            removed = False
            for edge in ((u, v), (v, u)):
                if edge in self.edges:
                    self.edges.remove(edge)
                    removed = True
                if edge in self.saved_cross_edges:
                    self.saved_cross_edges.remove(edge)

            if not removed:
                self.set_status("Такий зв'язок відсутній.", "#DC2626")
                return

            self.redraw_graph()
            self.set_status(f"Зв'язок {u} — {v} видалено.", "#16A34A")
        except ValueError:
            self.set_status("Введіть коректні числа для З і До.", "#DC2626")

    def on_run_clicked(self):
        if self.is_paused and self.steps_history:
            self.resume_search()
        else:
            self.start_new_search()

    def pause_search(self):
        if self.is_running and not self.is_paused:
            self.is_paused = True
            if self.after_id is not None:
                self.root.after_cancel(self.after_id)
                self.after_id = None
            self.btn_pause.config(state=tk.DISABLED)
            self.btn_run.config(text="▶ Продовжити", state=tk.NORMAL)
            self.set_status("Пошук призупинено (Пауза).", "#EAB308")

    def resume_search(self):
        self.is_paused = False
        self.is_running = True
        self.btn_run.config(state=tk.DISABLED)
        self.btn_pause.config(text="⏸ Пауза", state=tk.NORMAL)
        self.set_status("Продовження пошуку...", "#2563EB")
        self._schedule_next_step()

    def reset_search_state(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        self.is_running = False
        self.is_paused = False
        self.steps_history = []
        self.current_step_idx = 0
        self.search_result = None

        self.btn_run.config(text="▶ Запустити пошук", state=tk.NORMAL)
        self.btn_pause.config(text="⏸ Пауза", state=tk.DISABLED)
        self.set_status("Стан пошуку скинуто.", "#64748B")
        self.redraw_graph({})

    def _execute_search_algorithm(self, start, goal, adj, algo):
        t0 = time.perf_counter()
        cycles = 0
        expanded = 0
        found = False
        final_path = []
        node_status = {}
        steps = []

        if algo == "BFS":
            queue = deque([start])
            visited = {start}
            parent = {start: None}
            node_status[start] = "#FDBA74"
            steps.append(dict(node_status))

            while queue:
                cycles += 1
                curr = queue.popleft()
                node_status[curr] = "#86EFAC"
                expanded += 1
                steps.append(dict(node_status))

                if curr == goal:
                    found = True
                    break

                for nbr in adj.get(curr, []):
                    if nbr not in visited:
                        visited.add(nbr)
                        parent[nbr] = curr
                        queue.append(nbr)
                        node_status[nbr] = "#FDBA74"
                        steps.append(dict(node_status))

            if found:
                curr = goal
                while curr is not None:
                    final_path.append(curr)
                    curr = parent.get(curr)
                final_path.reverse()

        else:
            visited = set()
            found = False
            
            def dfs_rec(curr, current_path):
                nonlocal cycles, expanded, found, final_path
                cycles += 1
                visited.add(curr)
                node_status[curr] = "#86EFAC"
                expanded += 1
                steps.append(dict(node_status))

                if curr == goal:
                    found = True
                    final_path = list(current_path)
                    return True

                for nbr in adj.get(curr, []):
                    if nbr not in visited:
                        node_status[nbr] = "#FDBA74"
                        steps.append(dict(node_status))
                        if dfs_rec(nbr, current_path + [nbr]):
                            return True
                        
                return False

            node_status[start] = "#FDBA74"
            steps.append(dict(node_status))
            dfs_rec(start, [start])

        exec_time_ms = (time.perf_counter() - t0) * 1000.0

        result = {
            'found': found,
            'path': final_path,
            'cycles': cycles,
            'expanded': expanded,
            'exec_time_ms': exec_time_ms,
            'algo': algo
        }

        return steps, result

    def start_new_search(self):
        try:
            start = int(self.start_combo.get())
            goal = int(self.goal_combo.get())
        except ValueError:
            self.set_status("Оберіть коректні вершини Старт та Мета.", "#DC2626")
            return

        adj = self.get_adj_list()
        algo = self.algorithm_var.get()
        
        self.steps_history, self.search_result = self._execute_search_algorithm(start, goal, adj, algo)
        self.current_step_idx = 0

        self.is_running = True
        self.is_paused = False

        self.btn_run.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)
        self.set_status(f"Пошук {algo}: {start} ➔ {goal}...", "#2563EB")

        if self.steps_history:
            self.redraw_graph(highlighted_nodes=self.steps_history[0])
        self._schedule_next_step()

    def _schedule_next_step(self):
        delay = int(self.speed_scale.get())
        self.after_id = self.root.after(delay, self._step_search)

    def _step_search(self):
        if not self.is_running or self.is_paused:
            return

        self.current_step_idx += 1

        if self.current_step_idx < len(self.steps_history):
            current_status = self.steps_history[self.current_step_idx]
            self.redraw_graph(highlighted_nodes=current_status)
            self._schedule_next_step()
        else:
            self._finish_search()

    def _finish_search(self):
        res = self.search_result
        path_edges = set()
        final_node_status = dict(self.steps_history[-1]) if self.steps_history else {}

        if res['found']:
            p = res['path']
            for i in range(len(p) - 1):
                path_edges.add((p[i], p[i + 1]))
            for n in p:
                final_node_status[n] = "#3B82F6"
            self.redraw_graph(highlighted_nodes=final_node_status, path_edges=path_edges)

        self.is_running = False
        self.is_paused = False
        self.btn_run.config(text="▶ Запустити пошук", state=tk.NORMAL)
        self.btn_pause.config(text="⏸ Пауза", state=tk.DISABLED)

        self.set_status(f"Пошук {res['algo']} завершено", "#16A34A")
        self._show_results_dialog(res['algo'], res['found'], res['path'], 
                                  res['cycles'], res['expanded'], res['exec_time_ms'])

    def _show_results_dialog(self, algo, found, path, cycles, expanded, exec_time):
        res_window = tk.Toplevel(self.root)
        res_window.title(f"Результати {algo} пошуку")
        res_window.geometry("490x380")
        res_window.transient(self.root)

        f = ttk.Frame(res_window, padding=16)
        f.pack(fill=tk.BOTH, expand=True)

        status_text = "Шлях успішно знайдено!" if found else "Шлях не знайдено!"
        status_color = "#16A34A" if found else "#DC2626"

        lbl_status = tk.Label(f, text=status_text, font=("Arial", 12, "bold"), fg=status_color)
        lbl_status.pack(anchor=tk.W, pady=(0, 10))

        type_names = {
            "undirected": "Звичайний (Неорієнтований)",
            "directed": "Орієнтований (Орграф)",
            "tree": "Дерево"
        }

        details = [
            ("Алгоритм:", "В глибину (DFS)" if algo == "DFS" else "В ширину (BFS)"),
            ("Тип графа:", type_names.get(self.active_graph_type, self.active_graph_type)),
            ("Порядок обходу суміжних:", "За зростанням ID (1➔N)" if self.order_strategy.get() == "asc" else "За спаданням ID (N➔1)"),
            ("Кількість циклів (ітерацій):", f"{cycles}"),
            ("Кількість розкритих вершин:", f"{expanded}"),
            ("Час виконання алгоритму:", f"{exec_time:.4f} мс"),
            ("Довжина знайденого шляху:", f"{len(path) - 1} ребер" if found else "-"),
        ]

        for title, val in details:
            row = ttk.Frame(f)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=title, font=("Arial", 9, "bold")).pack(side=tk.LEFT)
            ttk.Label(row, text=val).pack(side=tk.RIGHT)

        ttk.Separator(f, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        ttk.Label(f, text="Знайдений шлях:", font=("Arial", 9, "bold")).pack(anchor=tk.W)

        path_str = " ➔ ".join(map(str, path)) if found else "Шлях відсутній"
        t_box = tk.Text(f, height=3, wrap=tk.WORD, font=("Consolas", 10))
        t_box.insert(tk.END, path_str)
        t_box.configure(state="disabled")
        t_box.pack(fill=tk.X, pady=4)

        ttk.Button(f, text="Закрити", command=res_window.destroy).pack(pady=8)

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphSearchApp(root)
    root.mainloop()