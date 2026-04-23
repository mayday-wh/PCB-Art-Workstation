import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, ttk
import tkinter.font as tkfont
from PIL import Image, ImageTk
import numpy as np
import os
import cv2

# ==========================================
# 样式辅助
# ==========================================
def get_main_font():
    families = tkfont.families()
    return "Microsoft YaHei" if "Microsoft YaHei" in families else "SimSun"

# ==========================================
# 模块 1: 色彩聚类映射
# ==========================================
class ColorMapperTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.palette = []
        self.original_img = None
        self.prev_img_tk = None
        self.scale_factor = 1.0
        self.setup_ui()

    def setup_ui(self):
        top_bar = tk.Frame(self, pady=10, bg="#f5f5f5")
        top_bar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(top_bar, text="📂 打开图片", command=self.load_image).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="🚀 执行转换", command=self.process_image, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="💾 保存结果", command=self.save_result).pack(side=tk.LEFT, padx=10)

        main_content = tk.Frame(self)
        main_content.pack(fill=tk.BOTH, expand=True)

        self.side_panel = tk.LabelFrame(main_content, text=" 已吸取色卡 ", padx=10, pady=10)
        self.side_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.side_panel.config(width=250); self.side_panel.pack_propagate(False)

        tk.Button(self.side_panel, text="清空所有颜色", command=self.clear_palette).pack(fill=tk.X, pady=5)
        
        canvas_container = tk.Frame(self.side_panel, bg="white", bd=1, relief=tk.SOLID)
        canvas_container.pack(fill=tk.BOTH, expand=True, pady=5)
        self.canvas_list = tk.Canvas(canvas_container, bg="white", highlightthickness=0)
        self.scroll_frame = tk.Frame(self.canvas_list, bg="white")
        self.canvas_list.create_window((0,0), window=self.scroll_frame, anchor="nw")
        self.canvas_list.pack(fill=tk.BOTH, expand=True)

        preview_frame = tk.Frame(main_content)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.left_label = tk.Label(preview_frame, text="原图 (点击吸色)", bg="#f9f9f9", cursor="cross", bd=1, relief=tk.SOLID)
        self.left_label.place(relx=0.01, rely=0.02, relwidth=0.48, relheight=0.96)
        self.left_label.bind("<Button-1>", self.on_click_eye_dropper)
        self.right_label = tk.Label(preview_frame, text="结果预览", bg="#f9f9f9", bd=1, relief=tk.SOLID)
        self.right_label.place(relx=0.51, rely=0.02, relwidth=0.48, relheight=0.96)

    def load_image(self):
        path = filedialog.askopenfilename()
        if path:
            self.original_img = Image.open(path).convert("RGB")
            self.update_view(self.original_img, self.left_label)

    def update_view(self, pil_img, label):
        self.update_idletasks()
        w, h = label.winfo_width(), label.winfo_height()
        if w < 10: w, h = 400, 300
        scale = min(w/pil_img.size[0], h/pil_img.size[1])
        if label == self.left_label: self.scale_factor = scale
        resized = pil_img.resize((int(pil_img.size[0]*scale), int(pil_img.size[1]*scale)), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized)
        if label == self.left_label: self.prev_img_tk = tk_img
        label.config(image=tk_img, text="")
        label.image = tk_img

    def on_click_eye_dropper(self, event):
        if not self.original_img or self.prev_img_tk is None: return
        iw, ih = self.prev_img_tk.width(), self.prev_img_tk.height()
        ox, oy = (self.left_label.winfo_width()-iw)/2, (self.left_label.winfo_height()-ih)/2
        if ox <= event.x <= ox+iw and oy <= event.y <= oy+ih:
            rx, ry = int((event.x-ox)/self.scale_factor), int((event.y-oy)/self.scale_factor)
            rgb = list(self.original_img.getpixel((rx, ry)))[:3]
            if rgb not in self.palette:
                self.palette.append(rgb); self.refresh_list()

    def refresh_list(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        for i, rgb in enumerate(self.palette):
            f = tk.Frame(self.scroll_frame, bg="white", pady=2)
            f.pack(fill=tk.X, padx=2)
            tk.Label(f, bg='#%02x%02x%02x'%tuple(rgb), width=3, relief=tk.SOLID, bd=1).pack(side=tk.LEFT, padx=5)
            tk.Label(f, text=f"{rgb}", font=("Consolas", 9), bg="white").pack(side=tk.LEFT)
            tk.Button(f, text="×", command=lambda idx=i: [self.palette.pop(idx), self.refresh_list()], fg="red", bd=0, bg="white").pack(side=tk.RIGHT, padx=5)
        self.canvas_list.config(scrollregion=self.canvas_list.bbox("all"))

    def clear_palette(self): self.palette = []; self.refresh_list()

    def process_image(self):
        if not self.original_img or not self.palette: return
        data = np.array(self.original_img); pixels = data.reshape(-1, 3); pal = np.array(self.palette)
        diff = pixels[:, np.newaxis, :] - pal[np.newaxis, :, :]
        dist_sq = np.sum(diff**2, axis=2); idx = np.argmin(dist_sq, axis=1)
        res = pal[idx].reshape(data.shape).astype(np.uint8)
        self.result_img = Image.fromarray(res)
        self.update_view(self.result_img, self.right_label)

    def save_result(self):
        if hasattr(self, 'result_img'):
            p = filedialog.asksaveasfilename(defaultextension=".png")
            if p: self.result_img.save(p)

# ==========================================
# 模块 2: 自动分色提取
# ==========================================
class ColorSeparatorTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.original_img = None
        self.unique_colors = []
        self.file_path = ""
        self.setup_ui()

    def setup_ui(self):
        top = tk.Frame(self, pady=10, bg="#f5f5f5")
        top.pack(side=tk.TOP, fill=tk.X)
        tk.Button(top, text="📂 打开聚类图", command=self.load_image).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text="⚙️ 批量导出层", command=self.save_layers, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=10)

        main = tk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)
        self.side = tk.LabelFrame(main, text=" 识别颜色 ", padx=10, pady=10)
        self.side.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.side.config(width=250); self.side.pack_propagate(False)

        self.preview = tk.Label(main, text="预览区", bg="#f9f9f9", bd=1, relief=tk.SOLID)
        self.preview.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_image(self):
        p = filedialog.askopenfilename()
        if p:
            self.file_path = p; self.original_img = Image.open(p).convert("RGB")
            self.show_preview(self.original_img); self.analyze()

    def analyze(self):
        for w in self.side.winfo_children(): w.destroy()
        data = np.array(self.original_img)
        self.unique_colors = np.unique(data.reshape(-1, 3), axis=0)
        for c in self.unique_colors:
            f = tk.Frame(self.side, pady=2); f.pack(fill=tk.X)
            tk.Label(f, bg='#%02x%02x%02x'%tuple(c), width=3, relief=tk.SOLID, bd=1).pack(side=tk.LEFT, padx=5)
            tk.Label(f, text=f"{list(c)}", font=("Arial", 8)).pack(side=tk.LEFT)

    def show_preview(self, img):
        self.update_idletasks()
        w, h = self.preview.winfo_width(), self.preview.winfo_height()
        if w < 10: w, h = 400, 300
        scale = min(w/img.size[0], h/img.size[1])
        res = img.resize((int(img.size[0]*scale), int(img.size[1]*scale)), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(res)
        self.preview.config(image=tk_img, text=""); self.preview.image = tk_img

    def save_layers(self):
        d = filedialog.askdirectory()
        if d:
            data = np.array(self.original_img); base = os.path.splitext(os.path.basename(self.file_path))[0]
            for i, c in enumerate(self.unique_colors):
                mask = np.all(data == c, axis=-1); out = np.zeros(data.shape[:2], dtype=np.uint8); out[mask] = 255
                Image.fromarray(out, mode='L').save(os.path.join(d, f"{base}_L{i}_{c}.png"))
            messagebox.showinfo("完成", "导出成功")

# ==========================================
# 模块 3: 逻辑运算去噪
# ==========================================
class ImageLogicTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.image_paths = []
        self.result_img = None
        self.setup_ui()

    def setup_ui(self):
        top = tk.Frame(self, pady=10, bg="#f5f5f5")
        top.pack(side=tk.TOP, fill=tk.X)
        tk.Button(top, text="➕ 添加图层", command=self.add).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text="🧹 清空列表", command=self.clear).pack(side=tk.LEFT, padx=10)
        tk.Button(top, text="🔀 合并去噪", command=self.run, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(top, text="💾 保存结果", command=self.save).pack(side=tk.LEFT, padx=10)

        main = tk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)
        side_frame = tk.LabelFrame(main, text=" 图层列表 ", padx=10, pady=10)
        side_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        side_frame.config(width=250); side_frame.pack_propagate(False)
        
        self.listbox = tk.Listbox(side_frame, bd=1, relief=tk.SOLID)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        self.preview = tk.Label(main, text="合成预览", bg="#f9f9f9", bd=1, relief=tk.SOLID)
        self.preview.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    def add(self):
        ps = filedialog.askopenfilenames(filetypes=[("PNG", "*.png")])
        for p in ps:
            if p not in self.image_paths:
                self.image_paths.append(p); self.listbox.insert(tk.END, os.path.basename(p))

    def clear(self):
        self.image_paths = []; self.listbox.delete(0, tk.END)
        self.preview.config(image="", text="暂无预览"); self.result_img = None

    def run(self):
        if not self.image_paths: return
        base = np.array(Image.open(self.image_paths[0]).convert("L"), dtype=np.uint32)
        for i in range(1, len(self.image_paths)):
            layer = np.array(Image.open(self.image_paths[i]).convert("L"), dtype=np.uint32)
            if layer.shape != base.shape:
                messagebox.showerror("错误", "尺寸不匹配")
                return
            base += layer
        final_np = np.where(base > 0, 255, 0).astype(np.uint8)
        denoised = cv2.medianBlur(final_np, 3)
        self.result_img = Image.fromarray(denoised)
        self.show_preview(self.result_img)

    def show_preview(self, img):
        self.update_idletasks()
        w, h = self.preview.winfo_width(), self.preview.winfo_height()
        if w < 10: w, h = 400, 300
        scale = min(w/img.size[0], h/img.size[1])
        res = img.resize((int(img.size[0]*scale), int(img.size[1]*scale)), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(res)
        self.preview.config(image=tk_img, text=""); self.preview.image = tk_img

    def save(self):
        if self.result_img:
            p = filedialog.asksaveasfilename(defaultextension=".png")
            if p: self.result_img.save(p)

# ==========================================
# 主窗体整合
# ==========================================
class PCBMasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PCB 艺术加工助手 v2")
        
        # 1. 动态设置窗口大小 (屏幕 60%)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        ww, wh = int(sw * 0.6), int(sh * 0.6)
        self.root.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
        
        self.font_family = get_main_font()
        self.base_font_size = 11  # 字号小一号
        # 应用全局字体，不使用加粗
        self.root.option_add("*Font", (self.font_family, self.base_font_size))

        style = ttk.Style()
        style.theme_use("clam") 
        
        # 颜色：温和深蓝灰 + 浅灰
        color_sel_bg = "#4b6584" 
        color_nor_bg = "#d1d8e0" 
        
        style.configure("TNotebook", background="#f5f5f5", borderwidth=0)
        
        # 标签页样式：不加粗，固定 Padding
        style.configure("TNotebook.Tab", 
                        font=(self.font_family, self.base_font_size), 
                        padding=[30, 10],   
                        background=color_nor_bg, 
                        foreground="#4b6584",
                        borderwidth=0,      
                        focuscolor="")      

        # 核心：完全禁止选中时的几何变形 (padding 和 expand 保持死锁定)
        style.map("TNotebook.Tab",
                  background=[("selected", color_sel_bg), ("active", "#a5b1c2")], 
                  foreground=[("selected", "#ffffff")],
                  padding=[("selected", [30, 10])], 
                  lightcolor=[("selected", color_sel_bg)],
                  darkcolor=[("selected", color_sel_bg)],
                  expand=[("selected", [0, 0, 0, 0])]) 

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.tab1 = ColorMapperTab(self.notebook)
        self.tab2 = ColorSeparatorTab(self.notebook)
        self.tab3 = ImageLogicTab(self.notebook)

        self.notebook.add(self.tab1, text="色彩聚类映射")
        self.notebook.add(self.tab2, text="自动分色提取")
        self.notebook.add(self.tab3, text="逻辑运算去噪")

if __name__ == "__main__":
    root = tk.Tk()
    # 调整 Scaling 因子 (1.2 在 0.6 倍窗口下比较清晰)
    root.tk.call('tk', 'scaling', 1.2) 
    app = PCBMasterApp(root)
    root.mainloop()