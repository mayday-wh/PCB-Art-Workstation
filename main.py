import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser, font as tkfont
from PIL import Image, ImageTk, ImageFilter
import numpy as np
import os
import json
import ctypes
import sys

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
APP_VERSION = "4.1"
BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "colors.json")

APP_BG = "#ECE4D8"
BAR_BG = "#D8C7B3"
PANEL_BG = "#EFE8DE"
SURFACE_BG = "#F8F4ED"
CARD_BG = "#FFFDF8"
PREVIEW_BG = "#F4EFE7"
TEXT_COLOR = "#352A24"
MUTED_TEXT = "#6F6259"
BORDER_COLOR = "#C8B6A2"
PRIMARY = "#7B5E4B"
SECONDARY = "#5F756D"
ACCENT = "#6F7F91"
SUCCESS = "#6C8B5E"
DANGER = "#B45C4E"
SELECTED = "#8D6E63"
TAB_IDLE = "#E3D4C2"
BUTTON_TEXT = "#FFF8EF"
FONT_UI = ("微软雅黑", 12)
FONT_UI_BOLD = ("微软雅黑", 12, "bold")
FONT_SMALL = ("微软雅黑", 11)
FONT_SMALL_BOLD = ("微软雅黑", 11, "bold")
FONT_SECTION = ("微软雅黑", 13, "bold")
FONT_PREVIEW = ("微软雅黑", 15, "bold")
FONT_MONO = ("Consolas", 11)
FONT_MONO_BOLD = ("Consolas", 11, "bold")
FONT_MONO_LARGE = ("Consolas", 13, "bold")
FONT_TAB = ("微软雅黑", 17, "bold")
UI_SCALE = 1.0
BASE_TK_SCALING = 1.75

def sx(value):
    """Scale fixed pixel values while keeping very small positive values visible."""
    scaled = int(round(value * UI_SCALE))
    if value > 0:
        return max(1, scaled)
    if value < 0:
        return min(-1, scaled)
    return 0

def sp(values):
    return tuple(sx(v) for v in values)

def configure_screen_scaling(root):
    """Apply one screen-based scale to the window, Tk fonts, and fixed pixel spacing."""
    global UI_SCALE
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    UI_SCALE = max(0.6, min(1.0, screen_w / 3840))

    root.tk.call("tk", "scaling", max(1.05, BASE_TK_SCALING * UI_SCALE))

    win_w = min(sx(2000), int(screen_w * 0.92))
    win_h = min(sx(1200), int(screen_h * 0.88))
    root.geometry(f"{win_w}x{win_h}+{(screen_w-win_w)//2}+{(screen_h-win_h)//2}")
    root.minsize(sx(1000), sx(700))

def button_style(bg=PRIMARY, fg=BUTTON_TEXT):
    return {
        "bg": bg,
        "fg": fg,
        "activebackground": bg,
        "activeforeground": fg,
        "relief": tk.FLAT,
        "bd": 0,
        "highlightthickness": 0,
        "cursor": "hand2"
    }

def large_checkbutton(parent, variable, bg=PANEL_BG):
    return tk.Checkbutton(
        parent,
        variable=variable,
        bg=bg,
        fg=TEXT_COLOR,
        activebackground=bg,
        activeforeground=TEXT_COLOR,
        selectcolor=SURFACE_BG,
        relief=tk.FLAT,
        bd=0,
        highlightthickness=0,
        cursor="hand2"
    )

def layer_bar(parent, layers, bg=CARD_BG):
    values = (list(layers) + [0] * 7)[:7]
    canvas_w = sx(116)
    canvas_h = sx(34)
    bar_w = sx(9)
    gap = sx(6)
    top = sx(4)
    bottom = canvas_h - sx(4)
    total_w = 7 * bar_w + 6 * gap
    x = max(sx(4), (canvas_w - total_w) // 2)
    canvas = tk.Canvas(parent, width=canvas_w, height=canvas_h, bg=bg, highlightthickness=0)
    for active in values:
        fill = PRIMARY if active else "#DDD1C5"
        outline = SELECTED if active else BORDER_COLOR
        canvas.create_rectangle(x, top, x + bar_w, bottom, fill=fill, outline=outline, width=1)
        x += bar_w + gap
    return canvas

def color_swatch(parent, color, bg=CARD_BG, width=34, height=24, outline=BORDER_COLOR):
    canvas = tk.Canvas(
        parent,
        width=sx(width),
        height=sx(height),
        bg=bg,
        bd=0,
        highlightthickness=0
    )
    canvas.create_rectangle(
        sx(1),
        sx(1),
        sx(width) - sx(1),
        sx(height) - sx(1),
        fill=color,
        outline=outline,
        width=sx(1)
    )
    return canvas

def rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

class RoundedButton(tk.Canvas):
    def __init__(self, master, text, command, bg, fg=BUTTON_TEXT, font=FONT_UI_BOLD, padx=14, pady=7, radius=12):
        self.text = text
        self.command = command
        self.fill = bg
        self.fg = fg
        self.button_font = font
        self.radius = sx(radius)
        measure_font = tkfont.Font(font=font)
        width = measure_font.measure(text) + sx(padx) * 2
        height = measure_font.metrics("linespace") + sx(pady) * 2
        super().__init__(
            master,
            width=width,
            height=height,
            bg=master.cget("bg"),
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )
        self.button_width = width
        self.button_height = height
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda _event: self._draw(hover=True))
        self.bind("<Leave>", lambda _event: self._draw(hover=False))
        self._draw()

    def _on_click(self, _event):
        if self.command:
            self.command()

    def _draw(self, hover=False):
        self.delete("all")
        inset = sx(1)
        outline = SELECTED if hover else self.fill
        rounded_rect(
            self,
            inset,
            inset,
            self.button_width - inset,
            self.button_height - inset,
            self.radius,
            fill=self.fill,
            outline=outline,
            width=sx(1)
        )
        self.create_text(
            self.button_width // 2,
            self.button_height // 2,
            text=self.text,
            fill=self.fg,
            font=self.button_font
        )

def rounded_button(parent, text, command, bg=PRIMARY, fg=BUTTON_TEXT, font=FONT_UI_BOLD, padx=14, pady=7, radius=12):
    return RoundedButton(parent, text, command, bg, fg=fg, font=font, padx=padx, pady=pady, radius=radius)

class ColorCheckBlock(tk.Canvas):
    def __init__(self, master, text, variable, font=FONT_UI_BOLD, width=132, height=42, radius=13):
        super().__init__(
            master,
            width=sx(width),
            height=sx(height),
            bg=master.cget("bg"),
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )
        self.text = text
        self.variable = variable
        self.block_font = font
        self.block_width = sx(width)
        self.block_height = sx(height)
        self.radius = sx(radius)
        self.bind("<Button-1>", self.toggle)
        self.variable.trace_add("write", lambda *_args: self._draw())
        self._draw()

    def toggle(self, _event=None):
        self.variable.set(0 if self.variable.get() else 1)

    def _draw(self):
        self.delete("all")
        selected = bool(self.variable.get())
        fill = SUCCESS if selected else SURFACE_BG
        outline = SUCCESS if selected else BORDER_COLOR
        fg = BUTTON_TEXT if selected else TEXT_COLOR
        inset = sx(1)
        rounded_rect(
            self,
            inset,
            inset,
            self.block_width - inset,
            self.block_height - inset,
            self.radius,
            fill=fill,
            outline=outline,
            width=sx(1)
        )
        self.create_text(
            self.block_width // 2,
            self.block_height // 2,
            text=self.text,
            fill=fg,
            font=self.block_font
        )

def rgb_to_hex(rgb):
    """将 RGB 数组转换为 #RRGGBB 格式。"""
    r, g, b = [int(c) for c in rgb[:3]]
    return f"#{r:02X}{g:02X}{b:02X}"

def nearest_palette_indices(pixels, palette, chunk_size=500000):
    """分块计算最近调色板索引，避免大图一次性生成过大的距离矩阵。"""
    pixels = np.asarray(pixels, dtype=np.int32)
    palette = np.asarray(palette, dtype=np.int32)
    idx = np.empty(pixels.shape[0], dtype=np.intp)

    for start in range(0, pixels.shape[0], chunk_size):
        end = min(start + chunk_size, pixels.shape[0])
        diff = pixels[start:end, np.newaxis, :] - palette[np.newaxis, :, :]
        dist = np.sum(diff * diff, axis=2)
        idx[start:end] = np.argmin(dist, axis=1)

    return idx

def init_db():
    """初始化 JSON 数据库，确保程序启动时数据路径有效。"""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

def load_recipes():
    """读取本地色卡数据库；文件为空或损坏时返回空列表，避免 UI 崩溃。"""
    init_db()
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def save_recipes(data):
    """写入本地色卡数据库。"""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==========================================
# 模块 1: 色卡录入 (Recipe Recorder)
# ==========================================
class RecipeRecorderTab(tk.Frame):
    """
    该模块负责通过实拍照片采样，建立 PCB 物理层叠与视觉颜色的对应表。
    """
    def __init__(self, master):
        super().__init__(master)
        self.configure(bg=APP_BG)
        self.ref_img = None        # 载入的原始图片对象
        self.scale_factor = 1.0     # 预览缩放比例，用于点击坐标还原到原图坐标
        self.temp_rgb = [128, 128, 128] # 当前选中的 RGB 颜色
        self.phys_layers = ["TS", "TM", "TL", "FR4", "BL", "BM", "BS"] # 7大物理层级
        self.preview_resize_job = None
        self.toolbar_wrapped = False
        self.toolbar_layout_job = None
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        """构建录入界面的 UI 布局"""
        # --- 顶部工具栏 ---
        top_bar = tk.Frame(self, bg=BAR_BG)
        top_bar.pack(side=tk.TOP, fill=tk.X)
        self.toolbar_line1 = tk.Frame(top_bar, pady=sx(10), bg=BAR_BG)
        self.toolbar_line2 = tk.Frame(top_bar, pady=sp((0, 10))[1], bg=BAR_BG)
        self.toolbar_line1.pack(side=tk.TOP, fill=tk.X)
        self.capture_group = tk.Frame(top_bar, bg=BAR_BG)
        self.layer_group = tk.Frame(top_bar, padx=sx(8), pady=sx(3), bg=BAR_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.save_group = tk.Frame(top_bar, bg=BAR_BG)
        self.capture_group.pack(in_=self.toolbar_line1, side=tk.LEFT)
        self.layer_group.pack(in_=self.toolbar_line1, side=tk.LEFT, padx=sp((0, 12)))
        self.save_group.pack(in_=self.toolbar_line1, side=tk.LEFT)

        rounded_button(self.capture_group, "载入照片", self.load_image, PRIMARY, padx=18, pady=8, radius=13).pack(side=tk.LEFT, padx=sx(15))

        self.mask_var = tk.StringVar(value="蓝色"); self.mode_var = tk.StringVar(value="有背光")
        filter_group = tk.Frame(self.capture_group, bg=BAR_BG)
        filter_group.pack(side=tk.LEFT, padx=sp((0, 8)))
        self.m_cb = ttk.Combobox(filter_group, textvariable=self.mask_var, values=["蓝色", "绿色", "黄色", "红色", "紫色", "白色", "黑色"], state="readonly", width=9, font=FONT_UI)
        self.m_cb.pack(side=tk.LEFT, padx=sx(5))
        self.m_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())
        self.mode_cb = ttk.Combobox(filter_group, textvariable=self.mode_var, values=["无背光", "有背光"], state="readonly", width=9, font=FONT_UI)
        self.mode_cb.pack(side=tk.LEFT, padx=sx(5))
        self.mode_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())

        self.cur_color_lab = tk.Label(self.capture_group, text="点击取色/色盘", bg=SURFACE_BG, fg=MUTED_TEXT, relief=tk.SOLID, bd=1, padx=sx(14), pady=sx(8), font=FONT_UI_BOLD, cursor="hand2")
        self.cur_color_lab.pack(side=tk.LEFT, padx=sp((4, 12)))
        self.cur_color_lab.bind("<Button-1>", self.pick_color_from_palette)

        self.layer_vars = []
        for i, name in enumerate(self.phys_layers):
            var = tk.IntVar(); self.layer_vars.append(var)
            if i == 3: var.set(1) # 默认勾选 FR4 基板层
            ColorCheckBlock(self.layer_group, name, var, font=FONT_MONO_BOLD, width=54, height=40, radius=11).pack(side=tk.LEFT, padx=sx(3))

        rounded_button(self.save_group, "录入当前色块配方", self.save_recipe, SECONDARY, padx=16, pady=8, radius=13).pack(side=tk.LEFT, padx=sx(8))
        top_bar.bind("<Configure>", self._schedule_toolbar_layout)
        self.after_idle(self._layout_toolbar)

        # --- 主显示区 (左右分栏) ---
        main_content = tk.Frame(self, bg=APP_BG)
        main_content.pack(fill=tk.BOTH, expand=True)

        # 左侧控制面板，保持紧凑宽度，把更多空间留给图片预览。
        self.side_panel = tk.Frame(main_content, padx=sx(16), pady=sx(15), width=sx(440), bg=PANEL_BG)
        self.side_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.side_panel.pack_propagate(False)

        # 本地数据库展示区 (带 Canvas 宽度同步逻辑)
        list_frame = tk.LabelFrame(self.side_panel, text=" 本地数据库 (分类筛选) ", padx=sx(10), pady=sx(10), font=FONT_SECTION, bg=PANEL_BG, fg=TEXT_COLOR, highlightbackground=BORDER_COLOR)
        list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=sx(5))
        
        self.list_canvas = tk.Canvas(list_frame, highlightthickness=0, bg=SURFACE_BG)
        self.scroll_y = tk.Scrollbar(list_frame, orient="vertical", command=self.list_canvas.yview)
        self.scroll_inner = tk.Frame(self.list_canvas, bg=SURFACE_BG)
        
        # 核心：通过绑定 Configure 确保列表条目宽度始终横向撑满 Canvas
        self.canvas_win = self.list_canvas.create_window((0, 0), window=self.scroll_inner, anchor="nw")
        self.list_canvas.bind('<Configure>', self._on_canvas_configure)
        self.scroll_inner.bind("<Configure>", lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all")))
        self.list_canvas.bind("<Enter>", self._bind_list_mousewheel)
        self.list_canvas.bind("<Leave>", self._unbind_list_mousewheel)
        self.scroll_inner.bind("<Enter>", self._bind_list_mousewheel)
        self.scroll_inner.bind("<Leave>", self._unbind_list_mousewheel)
        self.list_canvas.configure(yscrollcommand=self.scroll_y.set)
        self.list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 右侧照片预览
        self.preview_label = tk.Label(main_content, text="照片预览区", bg=PREVIEW_BG, fg=MUTED_TEXT, bd=1, relief=tk.SOLID, font=FONT_PREVIEW)
        self.preview_label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=sx(22), pady=sx(22))
        self.preview_label.bind("<Button-1>", self.on_click_eye_dropper)
        self.preview_label.bind("<Configure>", self._schedule_preview_resize)

    def _on_canvas_configure(self, event):
        """强制内部列表框架宽度等于 Canvas 宽度，解决缩放导致的宽度塌陷"""
        self.list_canvas.itemconfig(self.canvas_win, width=event.width)

    def _bind_list_mousewheel(self, event):
        self.list_canvas.bind_all("<MouseWheel>", self._on_list_mousewheel)

    def _unbind_list_mousewheel(self, event):
        self.list_canvas.unbind_all("<MouseWheel>")

    def _on_list_mousewheel(self, event):
        self.list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _schedule_toolbar_layout(self, event=None):
        if self.toolbar_layout_job:
            self.after_cancel(self.toolbar_layout_job)
        self.toolbar_layout_job = self.after(80, self._layout_toolbar)

    def _layout_toolbar(self):
        self.toolbar_layout_job = None
        self.update_idletasks()
        available = self.toolbar_line1.winfo_width()
        root_width = self.winfo_toplevel().winfo_width()
        if root_width > 1:
            available = min(available if available > 1 else root_width, max(1, root_width - sx(36)))
        needed = (
            self.capture_group.winfo_reqwidth()
            + self.layer_group.winfo_reqwidth()
            + self.save_group.winfo_reqwidth()
            + sx(24)
        )
        should_wrap = available > 1 and needed > available
        if should_wrap == self.toolbar_wrapped:
            return

        self.layer_group.pack_forget()
        self.save_group.pack_forget()
        self.toolbar_line2.pack_forget()
        if should_wrap:
            self.toolbar_line2.pack(side=tk.TOP, fill=tk.X)
            self.layer_group.pack(in_=self.toolbar_line2, side=tk.LEFT, padx=sp((15, 12)))
            self.save_group.pack(in_=self.toolbar_line2, side=tk.LEFT)
        else:
            self.layer_group.pack(in_=self.toolbar_line1, side=tk.LEFT, padx=sp((0, 12)))
            self.save_group.pack(in_=self.toolbar_line1, side=tk.LEFT)
        self.toolbar_wrapped = should_wrap

    def pick_color_from_palette(self, event):
        """弹出系统调色盘"""
        color = colorchooser.askcolor(title="选择颜色", initialcolor='#%02x%02x%02x'%tuple(self.temp_rgb))
        if color[0]:
            self.temp_rgb = [int(c) for c in color[0]]
            hex_color = rgb_to_hex(self.temp_rgb)
            self.cur_color_lab.config(bg=hex_color, text=f"选中色:{self.temp_rgb}  {hex_color}", fg=BUTTON_TEXT if sum(self.temp_rgb)<380 else TEXT_COLOR)

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

    def _schedule_preview_resize(self, event=None):
        if self.ref_img is None:
            return
        if self.preview_resize_job:
            self.after_cancel(self.preview_resize_job)
        self.preview_resize_job = self.after(120, self._refresh_preview_after_resize)

    def _refresh_preview_after_resize(self):
        self.preview_resize_job = None
        if self.ref_img is not None:
            self.show_preview(self.ref_img)

    def on_click_eye_dropper(self, event):
        """吸管工具：根据缩放比例计算并在原图上采样 RGB"""
        if self.ref_img is None: return
        lw, lh = self.preview_label.winfo_width(), self.preview_label.winfo_height()
        iw, ih = int(self.ref_img.size[0]*self.scale_factor), int(self.ref_img.size[1]*self.scale_factor)
        ox, oy = (lw-iw)/2, (lh-ih)/2
        if ox <= event.x <= ox+iw and oy <= event.y <= oy+ih:
            rx, ry = int((event.x-ox)/self.scale_factor), int((event.y-oy)/self.scale_factor)
            self.temp_rgb = list(self.ref_img.getpixel((rx, ry)))[:3]
            hex_color = rgb_to_hex(self.temp_rgb)
            self.cur_color_lab.config(bg=hex_color, text=f"选中色:{self.temp_rgb}  {hex_color}", fg=BUTTON_TEXT if sum(self.temp_rgb)<380 else TEXT_COLOR)

    def save_recipe(self):
        """配方存档逻辑"""
        recipe = {
            "mask": self.mask_var.get(), "mode": self.mode_var.get(), "rgb": self.temp_rgb,
            "layers": [v.get() for v in self.layer_vars],
            "layer_str": ",".join([self.phys_layers[i] for i, v in enumerate(self.layer_vars) if v.get()])
        }
        data = load_recipes()
        if any(
            r.get("mask") == recipe["mask"]
            and r.get("mode") == recipe["mode"]
            and list(r.get("layers", [])) == recipe["layers"]
            for r in data
        ):
            messagebox.showinfo("已存在", "当前分类下已经有相同层组合的色卡。")
            return
        data.append(recipe)
        save_recipes(data)
        self.refresh_list()

    def refresh_list(self):
        """实时渲染已保存的色卡列表，按分类自动筛选"""
        for w in self.scroll_inner.winfo_children(): w.destroy()
        all_data = load_recipes()
        filtered = [r for r in all_data if r["mask"] == self.mask_var.get() and r["mode"] == self.mode_var.get()]
        for r in filtered:
            f = tk.Frame(self.scroll_inner, bg=CARD_BG, pady=sx(7), bd=1, relief=tk.SOLID, highlightbackground=BORDER_COLOR)
            f.pack(fill=tk.X, pady=sx(3), padx=sx(6))
            hex_color = rgb_to_hex(r["rgb"])
            color_swatch(f, hex_color, width=32, height=32).pack(side=tk.LEFT, padx=sp((12, 8)))
            tk.Label(f, text=hex_color, font=FONT_MONO_BOLD, bg=CARD_BG, fg=TEXT_COLOR, width=9, anchor="w").pack(side=tk.LEFT)
            layer_bar(f, r.get("layers", []), bg=CARD_BG).pack(side=tk.LEFT, padx=sp((4, 8)))
            tk.Button(f, text="×", command=lambda item=r: self.delete_entry(item), font=FONT_UI_BOLD, fg=DANGER, bg=CARD_BG, activeforeground=DANGER, activebackground=CARD_BG, bd=0, cursor="hand2").pack(side=tk.RIGHT, padx=sx(14))
        self.list_canvas.config(scrollregion=self.list_canvas.bbox("all"))

    def delete_entry(self, item):
        """从数据库移除项目"""
        data = load_recipes()
        if item in data:
            data.remove(item)
            save_recipes(data)
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
        self.configure(bg=APP_BG)
        self.available_recipes = []
        self.mapping = {}
        self.original_img = None
        self.preview_img = None
        self.active_recipe_idx = None
        self.toolbar_wrapped = False
        self.toolbar_layout_job = None
        self.preview_resize_job = None
        
        # v3.3 标定控制变量[cite: 3]
        self.mark_tl = tk.IntVar(value=0)
        self.mark_tr = tk.IntVar(value=0)
        self.mark_bl = tk.IntVar(value=0)
        self.mark_br = tk.IntVar(value=0)
        self.mark_size_var = tk.StringVar(value="0")
        self.denoise_var = tk.IntVar(value=0)
        self.lceda_var = tk.IntVar(value=1)
        
        self.setup_ui()

    def setup_ui(self):
        """构建映射界面的 UI 布局"""
        top_bar = tk.Frame(self, bg=BAR_BG)
        top_bar.pack(side=tk.TOP, fill=tk.X)
        self.toolbar_line1 = tk.Frame(top_bar, pady=sx(10), bg=BAR_BG)
        self.toolbar_line2 = tk.Frame(top_bar, pady=sp((0, 10))[1], bg=BAR_BG)
        self.toolbar_line1.pack(side=tk.TOP, fill=tk.X)
        self.filter_group = tk.Frame(top_bar, bg=BAR_BG)
        self.action_group = tk.Frame(top_bar, bg=BAR_BG)
        self.settings_group = tk.Frame(top_bar, bg=BAR_BG)
        self.filter_group.pack(in_=self.toolbar_line1, side=tk.LEFT)
        self.action_group.pack(in_=self.toolbar_line1, side=tk.LEFT)
        self.settings_group.pack(in_=self.toolbar_line1, side=tk.LEFT)
        self.mask_var = tk.StringVar(value="蓝色"); self.mode_var = tk.StringVar(value="有背光")
        
        ttk.Combobox(self.filter_group, textvariable=self.mask_var, values=["蓝色", "绿色", "黄色", "红色", "紫色", "白色", "黑色"], state="readonly", width=10, font=FONT_UI).pack(side=tk.LEFT, padx=sx(10))
        ttk.Combobox(self.filter_group, textvariable=self.mode_var, values=["无背光", "有背光"], state="readonly", width=10, font=FONT_UI).pack(side=tk.LEFT, padx=sx(5))
        
        rounded_button(self.action_group, "提取色卡", self.fetch_recipes, PRIMARY, padx=16, pady=8, radius=13).pack(side=tk.LEFT, padx=sx(8))
        rounded_button(self.action_group, "载入图片", self.load_image, SECONDARY, padx=16, pady=8, radius=13).pack(side=tk.LEFT, padx=sx(8))
        rounded_button(self.action_group, "效果预览", self.process_alchemy, ACCENT, padx=16, pady=8, radius=13).pack(side=tk.LEFT, padx=sx(8))
        rounded_button(self.action_group, "导出图纸", self.export_layers, SUCCESS, padx=16, pady=8, radius=13).pack(side=tk.LEFT, padx=sx(8))

        # 原点设定移到顶部菜单，避免被长色卡列表挤到侧栏底部。
        self.cal_frame = tk.Frame(self.settings_group, padx=sx(10), pady=sx(4), bg=BAR_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.cal_frame.pack(side=tk.LEFT, padx=sp((8, 10)), pady=0)

        tk.Label(self.cal_frame, text="原点设定", bg=BAR_BG, fg=TEXT_COLOR, font=FONT_UI_BOLD).pack(side=tk.LEFT, padx=sp((0, 12)))

        mark_grid = tk.Frame(self.cal_frame, bg=BAR_BG)
        mark_grid.pack(side=tk.LEFT)

        corners = [("左上", self.mark_tl), ("右上", self.mark_tr), ("左下", self.mark_bl), ("右下", self.mark_br)]
        for i, (name, var) in enumerate(corners):
            mark_grid.columnconfigure(i, weight=1)
            ColorCheckBlock(mark_grid, name, var, font=FONT_UI_BOLD, width=58, height=40, radius=11).grid(row=0, column=i, sticky="ew", padx=sx(3))

        size_frame = tk.Frame(self.cal_frame, bg=BAR_BG)
        size_frame.pack(side=tk.LEFT, padx=sp((14, 0)))
        tk.Label(size_frame, text="边长(px)", bg=BAR_BG, fg=TEXT_COLOR, font=FONT_UI).pack(side=tk.LEFT, padx=sp((0, 6)))
        tk.Entry(size_frame, textvariable=self.mark_size_var, font=FONT_MONO_LARGE, width=6, justify=tk.CENTER).pack(side=tk.LEFT)

        denoise_frame = tk.Frame(self.settings_group, padx=sx(8), pady=sx(4), bg=BAR_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        denoise_frame.pack(side=tk.LEFT, padx=sp((0, 10)), pady=0)
        ColorCheckBlock(denoise_frame, "导出降噪", self.denoise_var).pack(side=tk.LEFT)

        lceda_frame = tk.Frame(self.settings_group, padx=sx(8), pady=sx(4), bg=BAR_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        lceda_frame.pack(side=tk.LEFT, padx=sp((0, 10)), pady=0)
        ColorCheckBlock(lceda_frame, "立创EDA", self.lceda_var).pack(side=tk.LEFT)
        top_bar.bind("<Configure>", self._schedule_toolbar_layout)
        self.after_idle(self._layout_toolbar)

        main = tk.Frame(self, bg=APP_BG)
        main.pack(fill=tk.BOTH, expand=True)

        # 带有滚动功能的侧边面板
        self.side_outer = tk.Frame(main, width=sx(440), bg=PANEL_BG)
        self.side_outer.pack(side=tk.LEFT, fill=tk.Y)
        self.side_outer.pack_propagate(False)
        
        self.side_canvas = tk.Canvas(self.side_outer, highlightthickness=0, bg=PANEL_BG)
        self.side_inner = tk.Frame(self.side_canvas, bg=PANEL_BG)
        
        self.side_canvas_win = self.side_canvas.create_window((0, 0), window=self.side_inner, anchor="nw")
        self.side_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.side_canvas.bind('<Configure>', lambda e: self.side_canvas.itemconfig(self.side_canvas_win, width=e.width))
        self.side_inner.bind("<Configure>", lambda e: self.side_canvas.configure(scrollregion=self.side_canvas.bbox("all")))
        self.side_canvas.bind("<Enter>", self._bind_mapping_mousewheel)
        self.side_canvas.bind("<Leave>", self._unbind_mapping_mousewheel)
        self.side_inner.bind("<Enter>", self._bind_mapping_mousewheel)
        self.side_inner.bind("<Leave>", self._unbind_mapping_mousewheel)

        # 映射配对区
        self.map_frame = tk.LabelFrame(self.side_inner, text=" 色彩映射区 ", padx=sx(15), pady=sx(16), font=FONT_SECTION, bg=PANEL_BG, fg=TEXT_COLOR, highlightbackground=BORDER_COLOR)
        self.map_frame.pack(side=tk.TOP, fill=tk.X, padx=sx(10), pady=sx(10))
        self.list_frame = tk.Frame(self.map_frame, bg=PANEL_BG)
        self.list_frame.pack(fill=tk.BOTH, expand=True)
        self.list_frame.bind("<Enter>", self._bind_mapping_mousewheel)
        self.list_frame.bind("<Leave>", self._unbind_mapping_mousewheel)

        # 双预览视窗
        preview_frame = tk.Frame(main, bg=APP_BG)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.left_label = tk.Label(preview_frame, text="原图预览", bg=PREVIEW_BG, fg=MUTED_TEXT, bd=1, relief=tk.SOLID, font=FONT_PREVIEW)
        self.left_label.place(relx=0.01, rely=0.02, relwidth=0.48, relheight=0.96)
        self.left_label.bind("<Button-1>", self.on_src_click)
        self.left_label.bind("<Configure>", self._schedule_preview_resize)
        self.right_label = tk.Label(preview_frame, text="效果预览", bg=PREVIEW_BG, fg=MUTED_TEXT, bd=1, relief=tk.SOLID, font=FONT_PREVIEW)
        self.right_label.place(relx=0.51, rely=0.02, relwidth=0.48, relheight=0.96)
        self.right_label.bind("<Configure>", self._schedule_preview_resize)

    def _schedule_toolbar_layout(self, event=None):
        if self.toolbar_layout_job:
            self.after_cancel(self.toolbar_layout_job)
        self.toolbar_layout_job = self.after(80, self._layout_toolbar)

    def _layout_toolbar(self):
        self.toolbar_layout_job = None
        self.update_idletasks()
        available = self.toolbar_line1.winfo_width()
        root_width = self.winfo_toplevel().winfo_width()
        if root_width > 1:
            available = min(available if available > 1 else root_width, max(1, root_width - sx(36)))
        needed = (
            self.filter_group.winfo_reqwidth()
            + self.action_group.winfo_reqwidth()
            + self.settings_group.winfo_reqwidth()
            + sx(24)
        )
        should_wrap = available > 1 and needed > available
        if should_wrap == self.toolbar_wrapped:
            return

        self.action_group.pack_forget()
        self.settings_group.pack_forget()
        self.toolbar_line2.pack_forget()
        self.action_group.pack(in_=self.toolbar_line1, side=tk.LEFT)
        if should_wrap:
            self.toolbar_line2.pack(side=tk.TOP, fill=tk.X)
            self.settings_group.pack(in_=self.toolbar_line2, side=tk.LEFT)
        else:
            self.settings_group.pack(in_=self.toolbar_line1, side=tk.LEFT)
        self.toolbar_wrapped = should_wrap

    def _bind_mapping_mousewheel(self, event):
        self.side_canvas.bind_all("<MouseWheel>", self._on_mapping_mousewheel)

    def _unbind_mapping_mousewheel(self, event):
        self.side_canvas.unbind_all("<MouseWheel>")

    def _on_mapping_mousewheel(self, event):
        self.side_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def fetch_recipes(self):
        """同步库色配方"""
        all_data = load_recipes()
        self.available_recipes = [r for r in all_data if r["mask"] == self.mask_var.get() and r["mode"] == self.mode_var.get()]
        self.mapping = {i: None for i in range(len(self.available_recipes))}
        self.active_recipe_idx = None
        self.left_label.config(highlightthickness=0)
        self.refresh_mapping_list(preserve_scroll=False)
        self.side_canvas.configure(scrollregion=self.side_canvas.bbox("all"))

    def refresh_mapping_list(self, preserve_scroll=True):
        """渲染映射关系列表"""
        scroll_pos = self.side_canvas.yview()[0] if preserve_scroll else 0
        for w in self.list_frame.winfo_children(): w.destroy()
        for i, r in enumerate(self.available_recipes):
            f = tk.Frame(self.list_frame, pady=sx(6), bd=1, relief=tk.SOLID, bg=CARD_BG, highlightbackground=BORDER_COLOR)
            f.pack(fill=tk.X, pady=sx(3), padx=sx(1))
            recipe_hex = rgb_to_hex(r["rgb"])
            mapped_rgb = self.mapping[i]
            mapped_hex = rgb_to_hex(mapped_rgb) if mapped_rgb else "未映射"

            color_swatch(f, recipe_hex, width=32, height=32).pack(side=tk.LEFT, padx=sp((8, 5)))
            tk.Label(f, text=recipe_hex, font=FONT_MONO_BOLD, bg=CARD_BG, fg=TEXT_COLOR, width=8, anchor="w").pack(side=tk.LEFT, padx=sp((0, 3)))
            rounded_button(f, "映射", lambda idx=i: self.set_active(idx), PRIMARY, font=FONT_SMALL_BOLD, padx=9, pady=4, radius=9).pack(side=tk.LEFT, padx=sp((2, 8)))
            if mapped_rgb:
                color_swatch(f, rgb_to_hex(mapped_rgb), width=32, height=32).pack(side=tk.LEFT, padx=sp((0, 5)))
            else:
                color_swatch(f, SURFACE_BG, width=32, height=32, outline="#DDD1C5").pack(side=tk.LEFT, padx=sp((0, 5)))
            tk.Label(f, text=mapped_hex, font=FONT_MONO_BOLD, bg=CARD_BG, fg=TEXT_COLOR if mapped_rgb else MUTED_TEXT, width=8, anchor="w").pack(side=tk.LEFT, padx=sp((0, 4)))
            tk.Button(
                f,
                text="取消",
                font=FONT_SMALL,
                command=lambda idx=i: self.clear_mapping(idx),
                state=tk.NORMAL if mapped_rgb else tk.DISABLED,
                fg=DANGER,
                bg=CARD_BG,
                activeforeground=DANGER,
                activebackground=CARD_BG,
                relief=tk.FLAT,
                bd=0,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=sp((0, 6)))
        self.side_canvas.configure(scrollregion=self.side_canvas.bbox("all"))
        self.side_canvas.yview_moveto(scroll_pos)

    def set_active(self, idx):
        """激活取色状态"""
        self.active_recipe_idx = idx
        self.left_label.config(highlightbackground=SELECTED, highlightthickness=sx(4))

    def clear_mapping(self, idx):
        """取消指定色卡的原图颜色映射。"""
        self.mapping[idx] = None
        if getattr(self, "active_recipe_idx", None) == idx:
            self.active_recipe_idx = None
            self.left_label.config(highlightthickness=0)
        self.refresh_mapping_list()

    def on_src_click(self, event):
        """原图色块采样"""
        if self.active_recipe_idx is None or not self.original_img: return
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
            self.preview_img = None
            self.mark_size_var.set(str(max(1, int(self.original_img.size[0] / 100)))) 
            self.right_label.config(image="", text="效果预览")
            self.right_label.image = None
            self.show_view(self.original_img, self.left_label)

    def show_view(self, img, label):
        self.update_idletasks()
        w, h = label.winfo_width(), label.winfo_height()
        if w < 10 or h < 10:
            w, h = 800, 600
        scale = min(w/img.size[0], h/img.size[1])
        tk_img = ImageTk.PhotoImage(img.resize((int(img.size[0]*scale), int(img.size[1]*scale)), Image.Resampling.LANCZOS))
        label.config(image=tk_img, text=""); label.image = tk_img

    def _schedule_preview_resize(self, event=None):
        if self.original_img is None and self.preview_img is None:
            return
        if self.preview_resize_job:
            self.after_cancel(self.preview_resize_job)
        self.preview_resize_job = self.after(120, self._refresh_previews_after_resize)

    def _refresh_previews_after_resize(self):
        self.preview_resize_job = None
        if self.original_img is not None:
            self.show_view(self.original_img, self.left_label)
        if self.preview_img is not None:
            self.show_view(self.preview_img, self.right_label)

    def process_alchemy(self):
        """色彩聚集核心算法：基于欧几里德距离的最近邻重采样"""
        if not self.original_img: return
        pairs = [(self.mapping[i], self.available_recipes[i]["rgb"]) for i in self.mapping if self.mapping[i]]
        if not pairs: return
        data = np.array(self.original_img); pixels = data.reshape(-1, 3)
        src_pal = np.array([p[0] for p in pairs], dtype=np.uint8)
        dst_pal = np.array([p[1] for p in pairs], dtype=np.uint8)
        idx = nearest_palette_indices(pixels, src_pal)
        res = dst_pal[idx].reshape(data.shape).astype(np.uint8)
        self.preview_img = Image.fromarray(res)
        self.show_view(self.preview_img, self.right_label)

    def export_layers(self):
        """
        物理层导出核心逻辑：
        v3.3 特色：跳过空图层（全黑）以及全覆盖图层（全白），仅保留有图案内容的中间层。[cite: 3]
        """
        if not self.original_img: return
        valid = [i for i in self.mapping if self.mapping[i]]
        if not valid: return
        d = filedialog.askdirectory()
        if not d: return
        lceda_mode = bool(self.lceda_var.get())
        out_dir = os.path.join(d, "立创EDA") if lceda_mode else d
        if lceda_mode:
            os.makedirs(out_dir, exist_ok=True)
        
        data = np.array(self.original_img); pixels = data.reshape(-1, 3)
        src_pal = np.array([self.mapping[i] for i in valid], dtype=np.uint8)
        idx = nearest_palette_indices(pixels, src_pal)
        
        names = ["TS", "TM", "TL", "BL", "BM", "BS"]; p_idxs = [0,1,2,4,5,6] # 排除固定的 FR4
        try:
            sz = max(0, int(self.mark_size_var.get()))
        except ValueError:
            sz = 0
        
        for i, pi in enumerate(p_idxs):
            layer_name = names[i]
            l_map = np.array([self.available_recipes[vi]["layers"][pi] for vi in valid])
            
            # --- v3.3 双向过滤逻辑 ---
            if not np.any(l_map > 0): continue    # 过滤空层[cite: 3]
            if np.all(l_map > 0): continue        # 过滤全覆盖层[cite: 3]
            
            # 生成 0/255 的黑白像素数据
            bw_data = (l_map[idx] * 255).reshape(data.shape[:2]).astype(np.uint8)
            h, w = bw_data.shape

            if self.denoise_var.get():
                bw_data = np.array(Image.fromarray(bw_data).filter(ImageFilter.MedianFilter(size=3)))

            if lceda_mode and layer_name in ("BL", "BM", "BS"):
                bw_data = np.fliplr(bw_data).copy()
            
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

            if lceda_mode:
                bw_data = 255 - bw_data
            
            Image.fromarray(bw_data).save(os.path.join(out_dir, f"Layer_{layer_name}.png"))
            
        denoise_text = "，并已应用导出降噪" if self.denoise_var.get() else ""
        if lceda_mode:
            messagebox.showinfo("完成", f"立创EDA导出成功：已自动过滤无图案的空层与全覆盖层，底层已左右翻转，图纸已反相，文件位于“立创EDA”文件夹{denoise_text}。")
        else:
            messagebox.showinfo("完成", f"导出成功：已自动过滤无图案的空层与全覆盖层{denoise_text}。")

# ==========================================
# 主程序生命周期管理
# ==========================================
class RoundedTab(tk.Canvas):
    def __init__(self, master, text, command, width, height, radius, font):
        super().__init__(
            master,
            width=width,
            height=height,
            bg=master.cget("bg"),
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )
        self.text = text
        self.command = command
        self.tab_width = width
        self.tab_height = height
        self.radius = radius
        self.tab_font = font
        self.selected = False
        self.bind("<Button-1>", lambda _event: self.command())
        self.bind("<Configure>", lambda _event: self._draw())
        self._draw()

    def set_selected(self, selected):
        self.selected = selected
        self._draw()

    def _draw(self):
        self.delete("all")
        fill = SELECTED if self.selected else TAB_IDLE
        outline = SELECTED if self.selected else BORDER_COLOR
        fg = BUTTON_TEXT if self.selected else TEXT_COLOR
        inset = sx(1)
        rounded_rect(
            self,
            inset,
            inset,
            self.tab_width - inset,
            self.tab_height - inset,
            self.radius,
            fill=fill,
            outline=outline,
            width=sx(1)
        )
        self.create_text(
            self.tab_width // 2,
            self.tab_height // 2,
            text=self.text,
            fill=fg,
            font=self.tab_font
        )

class TabbedPageHost(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=APP_BG)
        self.tabs = []
        self.pages = []
        self.active_index = None

        self.tab_bar = tk.Frame(self, bg=APP_BG)
        self.tab_bar.pack(side=tk.TOP, fill=tk.X, padx=sx(4), pady=sp((0, 8)))

        self.content = tk.Frame(self, bg=APP_BG)
        self.content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def add(self, page, text):
        index = len(self.pages)
        tab = RoundedTab(
            self.tab_bar,
            text=text,
            command=lambda idx=index: self.select(idx),
            width=sx(224),
            height=sx(64),
            radius=sx(19),
            font=FONT_TAB
        )
        tab.pack(side=tk.LEFT, padx=sp((0, 8)))
        self.tabs.append(tab)
        self.pages.append(page)

        if self.active_index is None:
            self.select(index)

    def select(self, index):
        if self.active_index == index:
            return
        if self.active_index is not None:
            self.pages[self.active_index].pack_forget()
            self.tabs[self.active_index].set_selected(False)
        self.active_index = index
        self.tabs[index].set_selected(True)
        self.pages[index].pack(fill=tk.BOTH, expand=True)

class PCBMasterApp:
    def __init__(self, root):
        init_db()
        self.root = root
        self.root.title(f"PCB 艺术助手 v{APP_VERSION}")
        self.root.configure(bg=APP_BG)
        
        # 屏幕适配：统一窗口、控件间距和 Tk 字体缩放。
        configure_screen_scaling(self.root)
        
        # 全局样式深度配置 (CSS 风格封装)
        style = ttk.Style(); style.theme_use("clam")
        
        # 下拉框高度同步修正：通过内边距 padding 强制撑起外框[cite: 3]
        style.configure(
            "TCombobox",
            padding=sx(9),
            font=FONT_UI,
            fieldbackground=SURFACE_BG,
            background=SURFACE_BG,
            foreground=TEXT_COLOR,
            arrowcolor=TEXT_COLOR,
            bordercolor=BORDER_COLOR,
            lightcolor=BORDER_COLOR,
            darkcolor=BORDER_COLOR
        )
        style.map("TCombobox", fieldbackground=[("readonly", SURFACE_BG)], selectbackground=[("readonly", BAR_BG)], selectforeground=[("readonly", TEXT_COLOR)])
        self.root.option_add('*TCombobox*Listbox.font', FONT_UI)
        self.root.option_add('*TCombobox*Listbox.background', SURFACE_BG)
        self.root.option_add('*TCombobox*Listbox.foreground', TEXT_COLOR)
        self.root.option_add('*TCombobox*Listbox.selectBackground', SELECTED)
        self.root.option_add('*TCombobox*Listbox.selectForeground', BUTTON_TEXT)

        self.notebook = TabbedPageHost(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=sx(12), pady=sx(12))
        
        # 加载核心功能模块
        self.notebook.add(RecipeRecorderTab(self.notebook.content), text="色卡录入")
        self.notebook.add(ColorMapperTab(self.notebook.content), text="色彩聚集")

if __name__ == "__main__":
    root = tk.Tk()
    app = PCBMasterApp(root)
    root.mainloop()
