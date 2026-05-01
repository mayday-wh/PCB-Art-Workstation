import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
import tkinter.font as tkfont
from PIL import Image, ImageTk, ImageFilter
import numpy as np
import os
import json
import ctypes

# ==========================================
# 0. 系统级高 DPI 适配
# ==========================================
try:
    # 启用高 DPI 意识，确保在 2K/4K 屏幕下界面不模糊且比例正确
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try: 
        # 兼容旧版 Windows 的 DPI 适配
        ctypes.windll.user32.SetProcessDPIAware()
    except: 
        pass

# 数据库文件名
DB_FILE = "colors.json"

def init_db():
    """初始化 JSON 数据库，如果文件不存在则创建一个空列表"""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

# ==========================================
# 模块 1: 色卡录入
# ==========================================
class RecipeRecorderTab(tk.Frame):
    """
    色卡录入模块类：用于通过照片采样或手动选色，将 PCB 物理叠层与 RGB 颜色绑定并存库。
    """
    def __init__(self, master):
        super().__init__(master)
        self.ref_img = None        # 存储当前载入的 PIL 图像对象
        self.scale_factor = 1.0     # 图像缩放比例，用于坐标换算
        self.temp_rgb = [128, 128, 128] # 当前选中的 RGB 颜色
        # PCB 物理叠层名称定义
        self.phys_layers = ["TS", "TM", "TL", "FR4", "BL", "BM", "BS"]
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        """初始化录入模块的 UI 布局"""
        # --- 顶部工具栏 ---
        top_bar = tk.Frame(self, pady=12, bg="#f5f5f5")
        top_bar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(top_bar, text="载入照片", command=self.load_image, font=("微软雅黑", 13)).pack(side=tk.LEFT, padx=15)

        # --- 主内容区域 (左右分栏) ---
        main_content = tk.Frame(self)
        main_content.pack(fill=tk.BOTH, expand=True)

        # 左侧面板：宽度固定为 450px
        self.side_panel = tk.Frame(main_content, padx=20, pady=15, width=450)
        self.side_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.side_panel.pack_propagate(False) # 禁止子组件挤压面板宽度

        # --- 配方录入区 (上部) ---
        setup_frame = tk.LabelFrame(self.side_panel, text=" 配方录入区 ", padx=15, pady=20, font=("微软雅黑", 13, "bold"))
        setup_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        # 下拉选择框容器
        header_f = tk.Frame(setup_frame)
        header_f.pack(fill=tk.X)
        # 使用 grid 权重让下拉框平分 450px 的侧边栏宽度
        header_f.columnconfigure(0, weight=1)
        header_f.columnconfigure(1, weight=1)

        self.mask_var = tk.StringVar(value="蓝色")
        self.mode_var = tk.StringVar(value="无背光")
        combo_style_font = ("微软雅黑", 13)
        
        # 阻焊颜色下拉框 (高度由全局样式 TCombobox 控制)
        self.m_cb = ttk.Combobox(header_f, textvariable=self.mask_var, values=["蓝色", "绿色", "黄色", "红色", "紫色", "白色", "黑色"], state="readonly", font=combo_style_font)
        self.m_cb.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.m_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())
        
        # 背光模式下拉框
        self.mode_cb = ttk.Combobox(header_f, textvariable=self.mode_var, values=["无背光", "有背光"], state="readonly", font=combo_style_font)
        self.mode_cb.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.mode_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())

        # 选中色显示/调色盘入口
        self.cur_color_lab = tk.Label(setup_frame, text="点击打开色盘/取色", bg="#d1d8e0", relief=tk.SOLID, bd=1, pady=16, font=("微软雅黑", 13, "bold"), cursor="hand2")
        self.cur_color_lab.pack(fill=tk.X, pady=20)
        self.cur_color_lab.bind("<Button-1>", self.pick_color_from_palette)

        # 物理层级复选框容器
        cb_container = tk.Frame(setup_frame)
        cb_container.pack(fill=tk.X, pady=10)
        self.layer_vars = []
        for i, name in enumerate(self.phys_layers):
            unit = tk.Frame(cb_container)
            unit.pack(side=tk.LEFT, expand=True)
            var = tk.IntVar()
            self.layer_vars.append(var)
            if i == 3: var.set(1) # 默认选中 FR4
            tk.Checkbutton(unit, variable=var).pack(side=tk.TOP)
            tk.Label(unit, text=name, font=("Consolas", 13), fg="#333").pack(side=tk.TOP)

        # 录入按钮
        tk.Button(setup_frame, text="录入当前色块配方", command=self.save_recipe, bg="#6B9FCA", fg="white", font=("微软雅黑", 13, "bold"), pady=12).pack(fill=tk.X, pady=20)

        # --- 本地数据库预览区 (中部) ---
        list_frame = tk.LabelFrame(self.side_panel, text=" 本地数据库 (分类筛选) ", padx=10, pady=10, font=("微软雅黑", 13, "bold"))
        list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        
        # 使用 Canvas + Scrollbar 实现可滚动的全宽列表
        self.list_canvas = tk.Canvas(list_frame, highlightthickness=0, bg="white")
        self.scroll_y = tk.Scrollbar(list_frame, orient="vertical", command=self.list_canvas.yview)
        self.scroll_inner = tk.Frame(self.list_canvas, bg="white")
        
        # 核心：将内部框架放入 Canvas 窗口，并绑定配置事件以同步宽度
        self.canvas_win = self.list_canvas.create_window((0, 0), window=self.scroll_inner, anchor="nw")
        self.list_canvas.bind('<Configure>', self._on_canvas_configure)
        
        self.list_canvas.configure(yscrollcommand=self.scroll_y.set)
        self.list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 右侧照片显示区
        self.preview_label = tk.Label(main_content, text="照片预览区", bg="#f9f9f9", bd=1, relief=tk.SOLID, font=("微软雅黑", 16))
        self.preview_label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=25, pady=25)
        self.preview_label.bind("<Button-1>", self.on_click_eye_dropper)

    def _on_canvas_configure(self, event):
        """核心修复：强制内部列表框架的宽度始终等于 Canvas 宽度，实现全宽显示"""
        self.list_canvas.itemconfig(self.canvas_win, width=event.width)

    def pick_color_from_palette(self, event):
        """调用系统调色盘选择颜色"""
        color = colorchooser.askcolor(title="选择颜色", initialcolor='#%02x%02x%02x'%tuple(self.temp_rgb))
        if color[0]:
            self.temp_rgb = [int(c) for c in color[0]]
            self.cur_color_lab.config(bg=color[1], text=f"选中色:{self.temp_rgb}", fg="white" if sum(self.temp_rgb)<380 else "black")

    def load_image(self):
        """载入外部照片并显示"""
        p = filedialog.askopenfilename()
        if p:
            self.ref_img = Image.open(p).convert("RGB")
            self.show_preview(self.ref_img)

    def show_preview(self, img):
        """将 PIL 图像按 Label 尺寸等比缩放显示"""
        self.update_idletasks()
        pw, ph = self.preview_label.winfo_width(), self.preview_label.winfo_height()
        if pw < 10: pw, ph = 800, 600
        self.scale_factor = min(pw/img.size[0], ph/img.size[1])
        res = img.resize((int(img.size[0]*self.scale_factor), int(img.size[1]*self.scale_factor)), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(res)
        self.preview_label.config(image=tk_img, text=""); self.preview_label.image = tk_img

    def on_click_eye_dropper(self, event):
        """吸管功能：点击照片预览区提取对应位置的 RGB 颜色"""
        if self.ref_img is None: return
        lw, lh = self.preview_label.winfo_width(), self.preview_label.winfo_height()
        iw, ih = int(self.ref_img.size[0]*self.scale_factor), int(self.ref_img.size[1]*self.scale_factor)
        ox, oy = (lw-iw)/2, (lh-ih)/2
        if ox <= event.x <= ox+iw and oy <= event.y <= oy+ih:
            rx, ry = int((event.x-ox)/self.scale_factor), int((event.y-oy)/self.scale_factor)
            self.temp_rgb = list(self.ref_img.getpixel((rx, ry)))[:3]
            self.cur_color_lab.config(bg='#%02x%02x%02x'%tuple(self.temp_rgb), text=f"选中色:{self.temp_rgb}", fg="white" if sum(self.temp_rgb)<380 else "black")

    def save_recipe(self):
        """将当前配方保存到 JSON 数据库"""
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
        """刷新数据库列表显示，并根据当前下拉选择进行实时筛选"""
        for w in self.scroll_inner.winfo_children(): w.destroy()
        if not os.path.exists(DB_FILE): return
        with open(DB_FILE, 'r', encoding='utf-8') as f: all_data = json.load(f)
        filtered = [r for r in all_data if r["mask"] == self.mask_var.get() and r["mode"] == self.mode_var.get()]
        for r in filtered:
            f = tk.Frame(self.scroll_inner, bg="white", pady=8, bd=1, relief=tk.GROOVE)
            f.pack(fill=tk.X, pady=3, padx=5)
            tk.Label(f, bg='#%02x%02x%02x'%tuple(r["rgb"]), width=4).pack(side=tk.LEFT, padx=12)
            # 这里的 text 宽度现在会随 Canvas 撑满
            tk.Label(f, text=f"{r['layer_str']}", font=("Arial", 12), bg="white", anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Button(f, text="×", command=lambda item=r: self.delete_entry(item), font=("Arial", 12, "bold"), fg="#d46e63", bg="white", bd=0, cursor="hand2").pack(side=tk.RIGHT, padx=15)
        self.list_canvas.config(scrollregion=self.list_canvas.bbox("all"))

    def delete_entry(self, item):
        """从 JSON 数据库中删除指定项"""
        with open(DB_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        if item in data:
            data.remove(item)
            with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
            self.refresh_list()

# ==========================================
# 模块 2: 色彩聚集
# ==========================================
class ColorMapperTab(tk.Frame):
    """
    色彩聚集模块：用于将艺术原图通过色卡库进行重采样，生成具备物理层级逻辑的效果图。
    """
    def __init__(self, master):
        super().__init__(master)
        self.available_recipes = []
        self.mapping = {}
        self.original_img = None
        self.setup_ui()

    def setup_ui(self):
        """初始化 UI 布局"""
        # --- 顶部功能栏 ---
        top_bar = tk.Frame(self, pady=12, bg="#f5f5f5")
        top_bar.pack(side=tk.TOP, fill=tk.X)
        self.mask_var = tk.StringVar(value="蓝色"); self.mode_var = tk.StringVar(value="无背光")
        combo_style_font = ("微软雅黑", 13)
        
        # 阻焊色下拉 (高度由 TCombobox 样式控制)
        m_cb = ttk.Combobox(top_bar, textvariable=self.mask_var, values=["蓝色", "绿色", "黄色", "红色", "紫色", "白色", "黑色"], state="readonly", width=10, font=combo_style_font)
        m_cb.pack(side=tk.LEFT, padx=10)
        
        # 背光下拉
        mode_cb = ttk.Combobox(top_bar, textvariable=self.mode_var, values=["无背光", "有背光"], state="readonly", width=10, font=combo_style_font)
        mode_cb.pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_bar, text="提取色卡", command=self.fetch_recipes, font=("微软雅黑", 13)).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="载入图片", command=self.load_image, font=("微软雅黑", 13)).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="效果预览", command=self.process_alchemy, bg="#5791C1", fg="white", font=("微软雅黑", 13, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="导出图纸", command=self.export_layers, bg="#6FBE72", fg="white", font=("微软雅黑", 13, "bold")).pack(side=tk.LEFT, padx=10)

        # --- 下部区域 ---
        main = tk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)

        # 左侧面板：色彩映射映射区
        self.side = tk.LabelFrame(main, text=" 色彩映射区 ", width=450, padx=15, pady=20, font=("微软雅黑", 13, "bold"))
        self.side.pack(side=tk.LEFT, fill=tk.Y)
        self.side.pack_propagate(False)
        self.list_frame = tk.Frame(self.side)
        self.list_frame.pack(fill=tk.BOTH, expand=True)

        # 右侧预览双栏
        preview_frame = tk.Frame(main)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.left_label = tk.Label(preview_frame, text="原图预览", bg="#f9f9f9", bd=1, relief=tk.SOLID, font=("微软雅黑", 16))
        self.left_label.place(relx=0.01, rely=0.02, relwidth=0.48, relheight=0.96)
        self.left_label.bind("<Button-1>", self.on_src_click)
        self.right_label = tk.Label(preview_frame, text="效果预览", bg="#f9f9f9", bd=1, relief=tk.SOLID, font=("微软雅黑", 16))
        self.right_label.place(relx=0.51, rely=0.02, relwidth=0.48, relheight=0.96)

    def fetch_recipes(self):
        """从库中根据当前选择筛选可用的色卡配方"""
        if not os.path.exists(DB_FILE): return
        with open(DB_FILE, 'r', encoding='utf-8') as f: all_data = json.load(f)
        self.available_recipes = [r for r in all_data if r["mask"] == self.mask_var.get() and r["mode"] == self.mode_var.get()]
        self.mapping = {i: None for i in range(len(self.available_recipes))}
        self.refresh_mapping_list()

    def refresh_mapping_list(self):
        """展示当前加载的配方列表及其与原图色的映射状态"""
        for w in self.list_frame.winfo_children(): w.destroy()
        for i, r in enumerate(self.available_recipes):
            f = tk.Frame(self.list_frame, pady=10, bd=1, relief=tk.GROOVE)
            f.pack(fill=tk.X, pady=3)
            tk.Label(f, bg='#%02x%02x%02x'%tuple(r["rgb"]), width=4).pack(side=tk.LEFT, padx=12)
            tk.Button(f, text="映射", font=("微软雅黑", 12), command=lambda idx=i: self.set_active(idx)).pack(side=tk.LEFT, padx=10)
            if self.mapping[i]:
                # 如果已选择映射颜色，则显示颜色块
                tk.Label(f, bg='#%02x%02x%02x'%tuple(self.mapping[i]), width=4).pack(side=tk.RIGHT, padx=12)

    def set_active(self, idx):
        """激活某一个配方，准备在原图上进行取色配对"""
        self.active_recipe_idx = idx
        self.left_label.config(highlightbackground="#cd5f53", highlightthickness=4)

    def on_src_click(self, event):
        """点击原图获取颜色，并将其与选定的物理配方建立映射关系"""
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
        """载入艺术原图"""
        p = filedialog.askopenfilename()
        if p:
            self.original_img = Image.open(p).convert("RGB")
            self.show_view(self.original_img, self.left_label)

    def show_view(self, img, label):
        """显示并自适应缩放图片"""
        self.update_idletasks()
        w, h = label.winfo_width(), label.winfo_height()
        scale = min(w/img.size[0], h/img.size[1])
        tk_img = ImageTk.PhotoImage(img.resize((int(img.size[0]*scale), int(img.size[1]*scale))))
        label.config(image=tk_img, text=""); label.image = tk_img

    def process_alchemy(self):
        """核心处理逻辑：根据色彩映射表对原图进行最近邻色彩重采样"""
        if not self.original_img: return
        pairs = [(self.mapping[i], self.available_recipes[i]["rgb"]) for i in self.mapping if self.mapping[i]]
        if not pairs: return
        data = np.array(self.original_img); pixels = data.reshape(-1, 3)
        src_pal = np.array([p[0] for p in pairs]); dst_pal = np.array([p[1] for p in pairs])
        # 计算欧氏距离，找到原图中每个像素最接近的映射源色
        dist = np.sum((pixels[:, np.newaxis, :] - src_pal[np.newaxis, :, :])**2, axis=2)
        idx = np.argmin(dist, axis=1)
        # 生成映射后的物理视觉图
        res = dst_pal[idx].reshape(data.shape).astype(np.uint8)
        self.show_view(Image.fromarray(res), self.right_label)

    def export_layers(self):
        """基于色彩聚集结果，拆分并导出 6 个物理层的黑白位图图纸"""
        valid = [i for i in self.mapping if self.mapping[i]]
        if not valid: return
        d = filedialog.askdirectory()
        if not d: return
        data = np.array(self.original_img); pixels = data.reshape(-1, 3)
        src_pal = np.array([self.mapping[i] for i in valid])
        dist = np.sum((pixels[:, np.newaxis, :] - src_pal[np.newaxis, :, :])**2, axis=2)
        idx = np.argmin(dist, axis=1)
        names = ["TS", "TM", "TL", "BL", "BM", "BS"]; p_idxs = [0,1,2,4,5,6] # 跳过 FR4
        for i, pi in enumerate(p_idxs):
            # 提取每个物理配方的第 pi 层状态 (0或1)
            l_map = np.array([self.available_recipes[vi]["layers"][pi] for vi in valid])
            bw = (l_map[idx] * 255).reshape(data.shape[:2]).astype(np.uint8)
            # 应用中值滤波平滑锯齿，并保存
            Image.fromarray(bw).filter(ImageFilter.MedianFilter(size=3)).save(os.path.join(d, f"Layer_{names[i]}.png"))
        messagebox.showinfo("完成", "物理层导出成功")

# ==========================================
# 模块 3: 原点标记
# ==========================================
class CalibrationTab(tk.Frame):
    """
    原点标记模块：用于在最终导出的黑白图纸上增加定位点，确保制板时的物理原点对齐。
    """
    def __init__(self, master):
        super().__init__(master)
        self.original_img = None
        self.setup_ui()

    def setup_ui(self):
        # 顶部工具栏
        top = tk.Frame(self, pady=12, bg="#f5f5f5")
        top.pack(side=tk.TOP, fill=tk.X)
        tk.Button(top, text="载入图片", command=self.load_image, font=("微软雅黑", 13)).pack(side=tk.LEFT, padx=15)
        tk.Button(top, text="生成预览", command=self.run_preview, bg="#7959B1", fg="white", font=("微软雅黑", 13, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text="保存结果", command=self.save_result, bg="#55b17b", fg="white", font=("微软雅黑", 13, "bold")).pack(side=tk.LEFT, padx=10)
        
        main = tk.Frame(self); main.pack(fill=tk.BOTH, expand=True)
        self.side = tk.LabelFrame(main, text=" 标定参数 ", width=450, padx=20, pady=25, font=("微软雅黑", 13, "bold"))
        self.side.pack(side=tk.LEFT, fill=tk.Y); self.side.pack_propagate(False)
        
        tk.Label(self.side, text="标定边长 (px):", font=("微软雅黑", 13)).pack(anchor="w")
        self.size_var = tk.StringVar(value="0")
        tk.Entry(self.side, textvariable=self.size_var, font=("Consolas", 15)).pack(fill=tk.X, pady=25)
        
        self.preview = tk.Label(main, text="效果预览区", bg="#f9f9f9", bd=1, relief=tk.SOLID, font=("微软雅黑", 16))
        self.preview.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=30, pady=30)

    def load_image(self):
        """载入黑白图纸"""
        p = filedialog.askopenfilename()
        if p:
            self.original_img = Image.open(p).convert("L")
            w = self.original_img.size[0]
            self.size_var.set(str(max(1, int(w / 100)))) # 默认设为 1/100 宽度
            self.show_view(self.original_img)

    def run_preview(self):
        """在图像四个角绘制标定框"""
        if not self.original_img: return
        try: sz = int(self.size_var.get())
        except: return
        img_np = np.array(self.original_img); h, w = img_np.shape
        sz = min(sz, h, w // 2)
        self.preview_np = img_np.copy()
        # 处理左上角和右上角
        for y in range(sz): self.preview_np[y, 0:sz-y] = 255
        for y in range(sz): self.preview_np[y, w-(sz-y):w] = 255
        self.show_view(Image.fromarray(self.preview_np))

    def save_result(self):
        """保存带标定的图纸"""
        if not hasattr(self, 'preview_np'): return
        p = filedialog.asksaveasfilename(defaultextension=".png")
        if p:
            Image.fromarray(self.preview_np).save(p)
            messagebox.showinfo("成功", "标定图片已保存")

    def show_view(self, img):
        """预览显示"""
        self.update_idletasks()
        w, h = self.preview.winfo_width(), self.preview.winfo_height()
        if w < 10: w, h = 800, 600
        scale = min(w/img.size[0], h/img.size[1])
        tk_img = ImageTk.PhotoImage(img.resize((int(img.size[0]*scale), int(img.size[1]*scale))))
        self.preview.config(image=tk_img, text=""); self.preview.image = tk_img

# ==========================================
# 主程序
# ==========================================
class PCBMasterApp:
    """
    应用程序主窗口类：负责整体样式配置和标签页管理。
    """
    def __init__(self, root):
        init_db() # 初始化 JSON 库
        self.root = root
        self.root.title("PCB 艺术助手 v3.1")
        
        # 窗口宽高设定为屏幕分辨率的 0.6 倍
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        ww, wh = int(sw * 0.6), int(sh * 0.6)
        self.root.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
        self.root.minsize(1024, 768)

        style = ttk.Style()
        style.theme_use("clam")
        
        # --- 下拉选择框 (Combobox) 样式修正 ---
        # 核心：通过定义内边距撑起高度，并设置字体使高度与普通按钮对齐
        style.configure("TCombobox", 
                        padding=11, 
                        font=("微软雅黑", 13))
        
        # 设置下拉列表弹出部分的字体
        self.root.option_add('*TCombobox*Listbox.font', ("微软雅黑", 13))

        # --- 标签页 (Notebook) 样式优化 ---
        style.configure("TNotebook.Tab", 
                        padding=[60, 22], 
                        font=("微软雅黑", 14, "bold"),
                        background="#dcdde1")
        
        # 锁定选中时的样式，禁止“变矮”或“缩放”抖动
        style.map("TNotebook.Tab",
                  background=[("selected", "#7081a6")],
                  foreground=[("selected", "white")],
                  padding=[("selected", [60, 22])],  
                  expand=[("selected", [0, 0, 0, 0])]) 

        # 初始化标签页管理器
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 挂载三个功能模块
        self.notebook.add(RecipeRecorderTab(self.notebook), text="色卡录入")
        self.notebook.add(ColorMapperTab(self.notebook), text="色彩聚集")
        self.notebook.add(CalibrationTab(self.notebook), text="原点标记")

if __name__ == "__main__":
    root = tk.Tk()
    # 针对高分屏设置全局 UI 缩放因子
    root.tk.call('tk', 'scaling', 1.75) 
    app = PCBMasterApp(root)
    root.mainloop()