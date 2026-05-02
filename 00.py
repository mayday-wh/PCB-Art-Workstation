import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
import tkinter.font as tkfont
from PIL import Image, ImageTk, ImageFilter
import numpy as np
import os
import json
import ctypes

# ==========================================
# 0. 系统级环境配置
# ==========================================
try:
    # 针对 Windows 平台的高 DPI 适配，防止 2K/4K 屏幕下界面模糊[cite: 3]
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except: pass

# 核心数据库文件，存储 RGB 与物理层 (TS, TM, TL, FR4, BL, BM, BS) 的对应关系
DB_FILE = "colors.json"

def init_db():
    """初始化 JSON 数据库，确保程序启动时数据路径有效[cite: 3]"""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

# ==========================================
# 模块 1: 色卡录入 (Recipe Recorder)
# ==========================================
class RecipeRecorderTab(tk.Frame):
    """
    该模块负责通过实拍照片采样，建立 PCB 物理层叠与视觉颜色的对应表。
    """
    def __init__(self, master):
        super().__init__(master)
        self.ref_img = None        # 载入的原始图片对象
        self.scale_factor = 1.0     # 预览缩放比例，用于点击坐标还原到原图坐标
        self.temp_rgb = [128, 128, 128] # 当前选中的 RGB 颜色
        self.phys_layers = ["TS", "TM", "TL", "FR4", "BL", "BM", "BS"] # 7大物理层级
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        """构建录入界面的 UI 布局"""
        # --- 顶部工具栏 ---
        top_bar = tk.Frame(self, pady=12, bg="#f5f5f5")
        top_bar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(top_bar, text="载入照片", command=self.load_image, font=("微软雅黑", 13)).pack(side=tk.LEFT, padx=15)

        # --- 主显示区 (左右分栏) ---
        main_content = tk.Frame(self)
        main_content.pack(fill=tk.BOTH, expand=True)

        # 左侧控制面板 (固定 450px 宽度)
        self.side_panel = tk.Frame(main_content, padx=20, pady=15, width=450)
        self.side_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.side_panel.pack_propagate(False)

        # 1. 配方录入区
        setup_frame = tk.LabelFrame(self.side_panel, text=" 配方录入区 ", padx=15, pady=20, font=("微软雅黑", 13, "bold"))
        setup_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        # 下拉框容器：使用 grid 实现平分对齐
        header_f = tk.Frame(setup_frame)
        header_f.pack(fill=tk.X)
        header_f.columnconfigure(0, weight=1); header_f.columnconfigure(1, weight=1)

        self.mask_var = tk.StringVar(value="蓝色"); self.mode_var = tk.StringVar(value="无背光")
        
        self.m_cb = ttk.Combobox(header_f, textvariable=self.mask_var, values=["蓝色", "绿色", "黄色", "红色", "紫色", "白色", "黑色"], state="readonly", font=("微软雅黑", 13))
        self.m_cb.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.m_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())
        
        self.mode_cb = ttk.Combobox(header_f, textvariable=self.mode_var, values=["无背光", "有背光"], state="readonly", font=("微软雅黑", 13))
        self.mode_cb.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.mode_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())

        # 选中色显示/调色盘入口
        self.cur_color_lab = tk.Label(setup_frame, text="点击打开色盘/取色", bg="#d1d8e0", relief=tk.SOLID, bd=1, pady=16, font=("微软雅黑", 13, "bold"), cursor="hand2")
        self.cur_color_lab.pack(fill=tk.X, pady=20)
        self.cur_color_lab.bind("<Button-1>", self.pick_color_from_palette)

        # 物理层级勾选框 (TS 到 BS)
        cb_container = tk.Frame(setup_frame)
        cb_container.pack(fill=tk.X, pady=10)
        self.layer_vars = []
        for i, name in enumerate(self.phys_layers):
            unit = tk.Frame(cb_container); unit.pack(side=tk.LEFT, expand=True)
            var = tk.IntVar(); self.layer_vars.append(var)
            if i == 3: var.set(1) # 默认勾选 FR4 基板层
            tk.Checkbutton(unit, variable=var).pack(side=tk.TOP)
            tk.Label(unit, text=name, font=("Consolas", 13), fg="#333").pack(side=tk.TOP)

        tk.Button(setup_frame, text="录入当前色块配方", command=self.save_recipe, bg="#6B9FCA", fg="white", font=("微软雅黑", 13, "bold"), pady=12).pack(fill=tk.X, pady=20)

        # 2. 本地数据库展示区 (带 Canvas 宽度同步逻辑)
        list_frame = tk.LabelFrame(self.side_panel, text=" 本地数据库 (分类筛选) ", padx=10, pady=10, font=("微软雅黑", 13, "bold"))
        list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        
        self.list_canvas = tk.Canvas(list_frame, highlightthickness=0, bg="white")
        self.scroll_y = tk.Scrollbar(list_frame, orient="vertical", command=self.list_canvas.yview)
        self.scroll_inner = tk.Frame(self.list_canvas, bg="white")
        
        # 核心：通过绑定 Configure 确保列表条目宽度始终横向撑满 Canvas
        self.canvas_win = self.list_canvas.create_window((0, 0), window=self.scroll_inner, anchor="nw")
        self.list_canvas.bind('<Configure>', self._on_canvas_configure)
        self.list_canvas.configure(yscrollcommand=self.scroll_y.set)
        self.list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 右侧照片预览
        self.preview_label = tk.Label(main_content, text="照片预览区", bg="#f9f9f9", bd=1, relief=tk.SOLID, font=("微软雅黑", 16))
        self.preview_label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=25, pady=25)
        self.preview_label.bind("<Button-1>", self.on_click_eye_dropper)

    def _on_canvas_configure(self, event):
        """强制内部列表框架宽度等于 Canvas 宽度，解决缩放导致的宽度塌陷"""
        self.list_canvas.itemconfig(self.canvas_win, width=event.width)

    def pick_color_from_palette(self, event):
        """弹出系统调色盘"""
        color = colorchooser.askcolor(title="选择颜色", initialcolor='#%02x%02x%02x'%tuple(self.temp_rgb))
        if color[0]:
            self.temp_rgb = [int(c) for c in color[0]]
            self.cur_color_lab.config(bg=color[1], text=f"选中色:{self.temp_rgb}", fg="white" if sum(self.temp_rgb)<380 else "black")

    def load_image(self):
        """载入色卡扫描件/照片"""
        p = filedialog.askopenfilename()
        if p:
            self.ref_img = Image.open(p).convert("RGB")
            self.show_preview(self.ref_img)

    def show_preview(self, img):
        """自适应显示图片预览"""
        self.update_idletasks()
        pw, ph = self.preview_label.winfo_width(), self.preview_label.winfo_height()
        if pw < 10: pw, ph = 800, 600
        self.scale_factor = min(pw/img.size[0], ph/img.size[1])
        res = img.resize((int(img.size[0]*self.scale_factor), int(img.size[1]*self.scale_factor)), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(res)
        self.preview_label.config(image=tk_img, text=""); self.preview_label.image = tk_img

    def on_click_eye_dropper(self, event):
        """吸管工具：根据缩放比例计算并在原图上采样 RGB"""
        if self.ref_img is None: return
        lw, lh = self.preview_label.winfo_width(), self.preview_label.winfo_height()
        iw, ih = int(self.ref_img.size[0]*self.scale_factor), int(self.ref_img.size[1]*self.scale_factor)
        ox, oy = (lw-iw)/2, (lh-ih)/2
        if ox <= event.x <= ox+iw and oy <= event.y <= oy+ih:
            rx, ry = int((event.x-ox)/self.scale_factor), int((event.y-oy)/self.scale_factor)
            self.temp_rgb = list(self.ref_img.getpixel((rx, ry)))[:3]
            self.cur_color_lab.config(bg='#%02x%02x%02x'%tuple(self.temp_rgb), text=f"选中色:{self.temp_rgb}", fg="white" if sum(self.temp_rgb)<380 else "black")

    def save_recipe(self):
        """配方存档逻辑"""
        recipe = {
            "mask": self.mask_var.get(), "mode": self.mode_var.get(), "rgb": self.temp_rgb,
            "layers": [v.get() for v in self.layer_vars],
            "layer_str": ",".join([self.phys_layers[i] for i, v in enumerate(self.layer_vars) if v.get()])
        }
        with open(DB_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        data.append(recipe)
        with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
        self.refresh_list()

    def refresh_list(self):
        """实时渲染已保存的色卡列表，按分类自动筛选"""
        for w in self.scroll_inner.winfo_children(): w.destroy()
        if not os.path.exists(DB_FILE): return
        with open(DB_FILE, 'r', encoding='utf-8') as f: all_data = json.load(f)
        filtered = [r for r in all_data if r["mask"] == self.mask_var.get() and r["mode"] == self.mode_var.get()]
        for r in filtered:
            f = tk.Frame(self.scroll_inner, bg="white", pady=8, bd=1, relief=tk.GROOVE)
            f.pack(fill=tk.X, pady=3, padx=5)
            tk.Label(f, bg='#%02x%02x%02x'%tuple(r["rgb"]), width=4).pack(side=tk.LEFT, padx=12)
            tk.Label(f, text=f"{r['layer_str']}", font=("Arial", 12), bg="white", anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Button(f, text="×", command=lambda item=r: self.delete_entry(item), font=("Arial", 12, "bold"), fg="#d46e63", bg="white", bd=0, cursor="hand2").pack(side=tk.RIGHT, padx=15)
        self.list_canvas.config(scrollregion=self.list_canvas.bbox("all"))

    def delete_entry(self, item):
        """从数据库移除项目"""
        with open(DB_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        if item in data:
            data.remove(item)
            with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
        self.refresh_list()

# ==========================================
# 模块 2: 色彩聚集 (Color Mapper)
# ==========================================
class ColorMapperTab(tk.Frame):
    """
    色彩映射模块：将原图色块聚集到物理层叠，并生成带标定的黑白生产图纸[cite: 3]。
    """
    def __init__(self, master):
        super().__init__(master)
        self.available_recipes = []
        self.mapping = {}
        self.original_img = None
        
        # v3.3 标定控制变量[cite: 3]
        self.mark_tl = tk.IntVar(value=0)
        self.mark_tr = tk.IntVar(value=0)
        self.mark_bl = tk.IntVar(value=0)
        self.mark_br = tk.IntVar(value=0)
        self.mark_size_var = tk.StringVar(value="0")
        
        self.setup_ui()

    def setup_ui(self):
        """构建映射界面的 UI 布局"""
        top_bar = tk.Frame(self, pady=12, bg="#f5f5f5")
        top_bar.pack(side=tk.TOP, fill=tk.X)
        self.mask_var = tk.StringVar(value="蓝色"); self.mode_var = tk.StringVar(value="无背光")
        
        ttk.Combobox(top_bar, textvariable=self.mask_var, values=["蓝色", "绿色", "黄色", "红色", "紫色", "白色", "黑色"], state="readonly", width=10, font=("微软雅黑", 13)).pack(side=tk.LEFT, padx=10)
        ttk.Combobox(top_bar, textvariable=self.mode_var, values=["无背光", "有背光"], state="readonly", width=10, font=("微软雅黑", 13)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_bar, text="提取色卡", command=self.fetch_recipes, font=("微软雅黑", 13)).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="载入图片", command=self.load_image, bg="#A472C5", fg="white",font=("微软雅黑", 13)).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="效果预览", command=self.process_alchemy, bg="#5791C1", fg="white", font=("微软雅黑", 13, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="导出图纸", command=self.export_layers, bg="#6FBE72", fg="white", font=("微软雅黑", 13, "bold")).pack(side=tk.LEFT, padx=10)

        main = tk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)

        # 带有滚动功能的侧边面板
        self.side_outer = tk.Frame(main, width=450, bg="#f0f0f0")
        self.side_outer.pack(side=tk.LEFT, fill=tk.Y)
        self.side_outer.pack_propagate(False)
        
        self.side_canvas = tk.Canvas(self.side_outer, highlightthickness=0, bg="#f0f0f0")
        self.side_scroll = tk.Scrollbar(self.side_outer, orient="vertical", command=self.side_canvas.yview)
        self.side_inner = tk.Frame(self.side_canvas, bg="#f0f0f0")
        
        self.side_canvas_win = self.side_canvas.create_window((0, 0), window=self.side_inner, anchor="nw")
        self.side_canvas.configure(yscrollcommand=self.side_scroll.set)
        self.side_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.side_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.side_canvas.bind('<Configure>', lambda e: self.side_canvas.itemconfig(self.side_canvas_win, width=e.width))

        # 映射配对区
        self.map_frame = tk.LabelFrame(self.side_inner, text=" 色彩映射区 ", padx=15, pady=20, font=("微软雅黑", 13, "bold"))
        self.map_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        self.list_frame = tk.Frame(self.map_frame)
        self.list_frame.pack(fill=tk.BOTH, expand=True)

        # v3.3 集成的原点标记区[cite: 3]
        self.cal_frame = tk.LabelFrame(self.side_inner, text=" 原点标记设置 ", padx=15, pady=20, font=("微软雅黑", 13, "bold"))
        self.cal_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        mark_grid = tk.Frame(self.cal_frame)
        mark_grid.pack(fill=tk.X)
        
        corners = [("左上", self.mark_tl), ("右上", self.mark_tr), ("左下", self.mark_bl), ("右下", self.mark_br)]
        for i, (name, var) in enumerate(corners):
            mark_grid.columnconfigure(i, weight=1)
            unit = tk.Frame(mark_grid); unit.grid(row=0, column=i, sticky="ew")
            tk.Checkbutton(unit, variable=var).pack(side=tk.TOP)
            tk.Label(unit, text=name, font=("微软雅黑", 11)).pack(side=tk.TOP)
            
        tk.Label(self.cal_frame, text="标定边长 (px):", font=("微软雅黑", 12)).pack(anchor="w", pady=(15, 0))
        tk.Entry(self.cal_frame, textvariable=self.mark_size_var, font=("Consolas", 14)).pack(fill=tk.X, pady=10)

        # 双预览视窗
        preview_frame = tk.Frame(main)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.left_label = tk.Label(preview_frame, text="原图预览", bg="#f9f9f9", bd=1, relief=tk.SOLID, font=("微软雅黑", 16))
        self.left_label.place(relx=0.01, rely=0.02, relwidth=0.48, relheight=0.96)
        self.left_label.bind("<Button-1>", self.on_src_click)
        self.right_label = tk.Label(preview_frame, text="效果预览", bg="#f9f9f9", bd=1, relief=tk.SOLID, font=("微软雅黑", 16))
        self.right_label.place(relx=0.51, rely=0.02, relwidth=0.48, relheight=0.96)

    def fetch_recipes(self):
        """同步库色配方"""
        if not os.path.exists(DB_FILE): return
        with open(DB_FILE, 'r', encoding='utf-8') as f: all_data = json.load(f)
        self.available_recipes = [r for r in all_data if r["mask"] == self.mask_var.get() and r["mode"] == self.mode_var.get()]
        self.mapping = {i: None for i in range(len(self.available_recipes))}
        self.refresh_mapping_list()
        self.side_canvas.configure(scrollregion=self.side_canvas.bbox("all"))

    def refresh_mapping_list(self):
        """渲染映射关系列表"""
        for w in self.list_frame.winfo_children(): w.destroy()
        for i, r in enumerate(self.available_recipes):
            f = tk.Frame(self.list_frame, pady=10, bd=1, relief=tk.GROOVE)
            f.pack(fill=tk.X, pady=3)
            tk.Label(f, bg='#%02x%02x%02x'%tuple(r["rgb"]), width=4).pack(side=tk.LEFT, padx=12)
            tk.Button(f, text="映射", font=("微软雅黑", 12), command=lambda idx=i: self.set_active(idx)).pack(side=tk.LEFT, padx=10)
            if self.mapping[i]: tk.Label(f, bg='#%02x%02x%02x'%tuple(self.mapping[i]), width=4).pack(side=tk.RIGHT, padx=12)

    def set_active(self, idx):
        """激活取色状态"""
        self.active_recipe_idx = idx
        self.left_label.config(highlightbackground="#cd5f53", highlightthickness=4)

    def on_src_click(self, event):
        """原图色块采样"""
        if not hasattr(self, 'active_recipe_idx') or self.active_recipe_idx is None or not self.original_img: return
        w, h = self.left_label.winfo_width(), self.left_label.winfo_height()
        sw, sh = self.original_img.size
        scale = min(w/sw, h/sh)
        ox, oy = (w-sw*scale)/2, (h-sh*scale)/2
        rx, ry = int((event.x-ox)/scale), int((event.y-oy)/scale)
        if 0 <= rx < sw and 0 <= ry < sh:
            self.mapping[self.active_recipe_idx] = list(self.original_img.getpixel((rx, ry)))[:3]
            self.refresh_mapping_list()

    def load_image(self):
        """原图载入并自动计算 1/100 标定尺寸[cite: 3]"""
        p = filedialog.askopenfilename()
        if p:
            self.original_img = Image.open(p).convert("RGB")
            self.mark_size_var.set(str(max(1, int(self.original_img.size[0] / 100)))) 
            self.show_view(self.original_img, self.left_label)

    def show_view(self, img, label):
        self.update_idletasks()
        w, h = label.winfo_width(), label.winfo_height()
        scale = min(w/img.size[0], h/img.size[1])
        tk_img = ImageTk.PhotoImage(img.resize((int(img.size[0]*scale), int(img.size[1]*scale))))
        label.config(image=tk_img, text=""); label.image = tk_img

    def process_alchemy(self):
        """色彩聚集核心算法：基于欧几里德距离的最近邻重采样"""
        if not self.original_img: return
        pairs = [(self.mapping[i], self.available_recipes[i]["rgb"]) for i in self.mapping if self.mapping[i]]
        if not pairs: return
        data = np.array(self.original_img); pixels = data.reshape(-1, 3)
        src_pal = np.array([p[0] for p in pairs]); dst_pal = np.array([p[1] for p in pairs])
        dist = np.sum((pixels[:, np.newaxis, :] - src_pal[np.newaxis, :, :])**2, axis=2)
        idx = np.argmin(dist, axis=1)
        res = dst_pal[idx].reshape(data.shape).astype(np.uint8)
        self.show_view(Image.fromarray(res), self.right_label)

    def export_layers(self):
        """
        物理层导出核心逻辑：
        v3.3 特色：跳过空图层（全黑）以及全覆盖图层（全白），仅保留有图案内容的中间层。[cite: 3]
        """
        valid = [i for i in self.mapping if self.mapping[i]]
        if not valid: return
        d = filedialog.askdirectory()
        if not d: return
        
        data = np.array(self.original_img); pixels = data.reshape(-1, 3)
        src_pal = np.array([self.mapping[i] for i in valid])
        dist = np.sum((pixels[:, np.newaxis, :] - src_pal[np.newaxis, :, :])**2, axis=2)
        idx = np.argmin(dist, axis=1)
        
        names = ["TS", "TM", "TL", "BL", "BM", "BS"]; p_idxs = [0,1,2,4,5,6] # 排除固定的 FR4
        sz = int(self.mark_size_var.get())
        
        for i, pi in enumerate(p_idxs):
            l_map = np.array([self.available_recipes[vi]["layers"][pi] for vi in valid])
            
            # --- v3.3 双向过滤逻辑 ---
            if not np.any(l_map > 0): continue    # 过滤空层[cite: 3]
            if np.all(l_map > 0): continue        # 过滤全覆盖层[cite: 3]
            
            # 生成 0/255 的黑白像素数据
            bw_data = (l_map[idx] * 255).reshape(data.shape[:2]).astype(np.uint8)
            h, w = bw_data.shape
            
            # 添加物理标定点（三角形定位符）[cite: 3]
            if sz > 0:
                s = min(sz, h, w // 2)
                if self.mark_tl.get():
                    for y in range(s): bw_data[y, 0:s-y] = 255
                if self.mark_tr.get():
                    for y in range(s): bw_data[y, w-(s-y):w] = 255
                if self.mark_bl.get():
                    for y in range(s): bw_data[h-s+y, 0:s-y] = 255
                if self.mark_br.get():
                    for y in range(s): bw_data[h-s+y, w-(s-y):w] = 255
            
            # 导出并应用中值滤波以平滑边缘锯齿
            Image.fromarray(bw_data).filter(ImageFilter.MedianFilter(size=3)).save(os.path.join(d, f"Layer_{names[i]}.png"))
            
        messagebox.showinfo("完成", "导出成功：已自动过滤无图案的空层与全覆盖层。")

# ==========================================
# 主程序生命周期管理
# ==========================================
class PCBMasterApp:
    def __init__(self, root):
        init_db()
        self.root = root
        self.root.title("PCB 艺术助手 v3.2")
        
        # 0.6x 屏幕比例的窗口初始化逻辑[cite: 3]
        sw = self.root.winfo_screenwidth(); sh = self.root.winfo_screenheight()
        ww, wh = int(sw * 0.6), int(sh * 0.6)
        self.root.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
        self.root.minsize(1024, 768)
        
        # 全局样式深度配置 (CSS 风格封装)
        style = ttk.Style(); style.theme_use("clam")
        
        # 下拉框高度同步修正：通过内边距 padding 强制撑起外框[cite: 3]
        style.configure("TCombobox", padding=11, font=("微软雅黑", 13))
        self.root.option_add('*TCombobox*Listbox.font', ("微软雅黑", 13))
        
        # 标签页 Tab 样式锁定：禁止选中时的形变
        style.configure("TNotebook.Tab", padding=[60, 22], font=("微软雅黑", 14, "bold"), background="#dcdde1")
        style.map("TNotebook.Tab", background=[("selected", "#7081a6")], foreground=[("selected", "white")], padding=[("selected", [60, 22])], expand=[("selected", [0, 0, 0, 0])]) 

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 加载核心功能模块
        self.notebook.add(RecipeRecorderTab(self.notebook), text="色卡录入")
        self.notebook.add(ColorMapperTab(self.notebook), text="色彩聚集")

if __name__ == "__main__":
    root = tk.Tk()
    # 全局 UI 缩放因子设置，完美适配 Windows 10/11 的缩放百分比[cite: 3]
    root.tk.call('tk', 'scaling', 1.75) 
    app = PCBMasterApp(root)
    root.mainloop()