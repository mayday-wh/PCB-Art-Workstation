import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, ttk
import tkinter.font as tkfont
from PIL import Image, ImageTk
import numpy as np
import json
import os

# ==========================================
# 样式辅助：获取系统合适的字体
# ==========================================
def get_main_font():
    families = tkfont.families()
    # 优先使用微软雅黑，其次宋体
    font_name = "Microsoft YaHei" if "Microsoft YaHei" in families else "SimSun"
    return font_name

# ==========================================
# 模块 1: 像素色卡转换 (聚类映射)
# ==========================================
class ColorMapperTab(tk.Frame):
    """
    功能：打开原图，通过吸色或调色盘建立色卡，将图片像素归类到最接近的色卡颜色。
    """
    def __init__(self, master):
        super().__init__(master)
        self.palette = []       # 存储色卡 [R, G, B] 列表
        self.original_img = None
        self.prev_img_tk = None
        self.scale_factor = 1.0 # 原图与预览图的缩放比例
        self.is_eye_dropper_on = tk.BooleanVar(value=True)
        self.setup_ui()

    def setup_ui(self):
        # 顶部操作按钮
        top_bar = tk.Frame(self, pady=5, bg="#f0f0f0")
        top_bar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(top_bar, text="📂 打开图片", command=self.load_image).pack(side=tk.LEFT, padx=5)
        tk.Button(top_bar, text="🚀 执行聚类", command=self.process_image, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(top_bar, text="💾 保存结果", command=self.save_result).pack(side=tk.LEFT, padx=5)

        # 主显示区域
        main_content = tk.Frame(self)
        main_content.pack(fill=tk.BOTH, expand=True)

        # 左侧：色卡管理面板
        side_panel = tk.LabelFrame(main_content, text=" 色卡管理与方案 ", padx=5, pady=5)
        side_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        side_panel.config(width=260); side_panel.pack_propagate(False)

        # 方案导入导出按钮
        ctrl = tk.Frame(side_panel)
        ctrl.pack(fill=tk.X)
        tk.Button(ctrl, text="手动取色", command=self.add_color_picker).grid(row=0, column=0, sticky="ew")
        tk.Button(ctrl, text="清空方案", command=self.clear_palette).grid(row=0, column=1, sticky="ew")
        tk.Button(ctrl, text="导入预设", command=self.import_scheme).grid(row=1, column=0, sticky="ew")
        tk.Button(ctrl, text="保存预设", command=self.export_scheme).grid(row=1, column=1, sticky="ew")
        ctrl.columnconfigure((0,1), weight=1)

        tk.Checkbutton(side_panel, text="启用原图点击吸色", variable=self.is_eye_dropper_on).pack(pady=5)

        # 颜色列表显示区
        self.canvas_list = tk.Canvas(side_panel, bg="white", highlightthickness=0)
        self.scroll_frame = tk.Frame(self.canvas_list, bg="white")
        self.canvas_list.create_window((0,0), window=self.scroll_frame, anchor="nw")
        self.canvas_list.pack(fill=tk.BOTH, expand=True)

        # 右侧：预览区 (左原图，右结果)
        preview_frame = tk.Frame(main_content)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.left_label = tk.Label(preview_frame, text="原图 (点击吸色)", bg="#f9f9f9", cursor="cross", bd=1, relief=tk.SOLID)
        self.left_label.place(relx=0.01, rely=0.05, relwidth=0.48, relheight=0.9)
        self.left_label.bind("<Button-1>", self.on_click_eye_dropper)

        self.right_label = tk.Label(preview_frame, text="结果预览", bg="#f9f9f9", bd=1, relief=tk.SOLID)
        self.right_label.place(relx=0.51, rely=0.05, relwidth=0.48, relheight=0.9)

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("图像文件", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.original_img = Image.open(path).convert("RGB")
            self.update_view(self.original_img, self.left_label)

    def update_view(self, pil_img, label):
        """通用预览图更新函数"""
        self.update_idletasks()
        w, h = label.winfo_width(), label.winfo_height()
        if w < 10: w, h = 400, 600
        scale = min(w/pil_img.size[0], h/pil_img.size[1])
        if label == self.left_label: self.scale_factor = scale
        resized = pil_img.resize((int(pil_img.size[0]*scale), int(pil_img.size[1]*scale)), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized)
        if label == self.left_label: self.prev_img_tk = tk_img
        label.config(image=tk_img, text="")
        label.image = tk_img

    def on_click_eye_dropper(self, event):
        """点击原图吸色逻辑"""
        if not self.is_eye_dropper_on.get() or not self.original_img: return
        iw, ih = self.prev_img_tk.width(), self.prev_img_tk.height()
        # 计算图片居中偏移
        ox, oy = (self.left_label.winfo_width()-iw)/2, (self.left_label.winfo_height()-ih)/2
        if ox <= event.x <= ox+iw and oy <= event.y <= oy+ih:
            rx, ry = int((event.x-ox)/self.scale_factor), int((event.y-oy)/self.scale_factor)
            rgb = list(self.original_img.getpixel((rx, ry)))
            if rgb not in self.palette:
                self.palette.append(rgb); self.refresh_list()

    def refresh_list(self):
        """更新色卡列表 UI"""
        for w in self.scroll_frame.winfo_children(): w.destroy()
        for i, rgb in enumerate(self.palette):
            f = tk.Frame(self.scroll_frame, bg="white")
            f.pack(fill=tk.X, padx=2, pady=1)
            tk.Label(f, bg='#%02x%02x%02x'%tuple(rgb), width=2, relief=tk.SOLID, bd=1).pack(side=tk.LEFT)
            tk.Label(f, text=f"{rgb}", font=("Consolas", 9), bg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(f, text="×", command=lambda idx=i: [self.palette.pop(idx), self.refresh_list()], fg="red", bd=0, bg="white").pack(side=tk.RIGHT)
        self.canvas_list.config(scrollregion=self.canvas_list.bbox("all"))

    def add_color_picker(self):
        c = colorchooser.askcolor()
        if c[0]: 
            rgb = [int(x) for x in c[0]]
            if rgb not in self.palette: self.palette.append(rgb); self.refresh_list()

    def clear_palette(self): 
        self.palette = []; self.refresh_list()

    def import_scheme(self):
        p = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if p:
            with open(p, 'r') as f: self.palette = json.load(f)
            self.refresh_list()

    def export_scheme(self):
        p = filedialog.asksaveasfilename(defaultextension=".json")
        if p:
            with open(p, 'w') as f: json.dump(self.palette, f)

    def process_image(self):
        """核心：聚类映射算法"""
        if not self.original_img or not self.palette: return
        data = np.array(self.original_img)
        pixels = data.reshape(-1, 3); pal = np.array(self.palette)
        # 计算欧式距离平方
        diff = pixels[:, None, :] - pal[None, :, :]
        dist = np.sum(diff**2, axis=2)
        idx = np.argmin(dist, axis=1)
        res = pal[idx].reshape(data.shape).astype(np.uint8)
        self.result_img = Image.fromarray(res)
        self.update_view(self.result_img, self.right_label)

    def save_result(self):
        if hasattr(self, 'result_img'):
            p = filedialog.asksaveasfilename(defaultextension=".png")
            if p: self.result_img.save(p)

# ==========================================
# 模块 2: 自动分色提取 (单色层分离)
# ==========================================
class ColorSeparatorTab(tk.Frame):
    """
    功能：识别已聚类图片的唯一颜色，并为每种颜色生成一张黑底白图（遮罩层）。
    """
    def __init__(self, master):
        super().__init__(master)
        self.original_img = None
        self.unique_colors = []
        self.file_path = ""
        self.setup_ui()

    def setup_ui(self):
        top = tk.Frame(self, pady=5, bg="#f0f0f0")
        top.pack(side=tk.TOP, fill=tk.X)
        tk.Button(top, text="📂 打开聚类后的图", command=self.load_image).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="⚙️ 批量导出各颜色层", command=self.save_layers, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)

        main = tk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)
        
        self.side = tk.LabelFrame(main, text=" 识别到的颜色层 ", width=220)
        self.side.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.side.pack_propagate(False)

        self.preview = tk.Label(main, text="分色预览区", bg="#f0f0f0", bd=1, relief=tk.SOLID)
        self.preview.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    def load_image(self):
        p = filedialog.askopenfilename()
        if p:
            self.file_path = p
            self.original_img = Image.open(p).convert("RGB")
            self.show_preview(self.original_img)
            self.analyze_colors()

    def analyze_colors(self):
        """提取图中所有不重复的颜色"""
        for w in self.side.winfo_children(): w.destroy()
        data = np.array(self.original_img)
        self.unique_colors = np.unique(data.reshape(-1, 3), axis=0)
        for c in self.unique_colors:
            f = tk.Frame(self.side)
            f.pack(fill=tk.X, pady=1)
            tk.Label(f, bg='#%02x%02x%02x'%tuple(c), width=2, relief=tk.SOLID, bd=1).pack(side=tk.LEFT, padx=2)
            tk.Label(f, text=f"RGB {list(c)}", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

    def show_preview(self, img):
        self.update_idletasks()
        w, h = self.preview.winfo_width(), self.preview.winfo_height()
        if w < 10: w, h = 600, 400
        scale = min(w/img.size[0], h/img.size[1])
        resized = img.resize((int(img.size[0]*scale), int(img.size[1]*scale)), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized)
        self.preview.config(image=tk_img, text="")
        self.preview.image = tk_img

    def save_layers(self):
        """生成分色图：颜色匹配处为白(255)，其余为黑(0)"""
        d = filedialog.askdirectory(title="选择保存目录")
        if d:
            data = np.array(self.original_img)
            base = os.path.splitext(os.path.basename(self.file_path))[0]
            for i, c in enumerate(self.unique_colors):
                mask = np.all(data == c, axis=-1)
                out = np.zeros(data.shape[:2], dtype=np.uint8)
                out[mask] = 255
                Image.fromarray(out, mode='L').save(os.path.join(d, f"{base}_Layer{i}_RGB_{c[0]}_{c[1]}_{c[2]}.png"))
            messagebox.showinfo("完成", f"已导出 {len(self.unique_colors)} 个图层文件")

# ==========================================
# 模块 3: 逻辑运算合成 (黑白层叠加)
# ==========================================
class ImageLogicTab(tk.Frame):
    """
    功能：将多个黑白层合并。全黑保持黑，有任何一层是白则结果为白。
    """
    def __init__(self, master):
        super().__init__(master)
        self.image_paths = [] # 待合成的图片列表
        self.result_img = None
        self.setup_ui()

    def setup_ui(self):
        top = tk.Frame(self, pady=5, bg="#f0f0f0")
        top.pack(side=tk.TOP, fill=tk.X)
        tk.Button(top, text="➕ 添加分色图层", command=self.add_image).pack(side=tk.LEFT, padx=5)
        # 清空列表功能
        tk.Button(top, text="🧹 清空列表", command=self.clear_list).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="🔀 执行叠加运算", command=self.run_logic, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="💾 保存合成结果", command=self.save_result).pack(side=tk.LEFT, padx=5)

        main = tk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)
        
        list_frame = tk.LabelFrame(main, text=" 已选择的图层 ", width=250)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        list_frame.pack_propagate(False)
        
        self.listbox = tk.Listbox(list_frame, font=("Arial", 9))
        self.listbox.pack(fill=tk.BOTH, expand=True)

        self.preview = tk.Label(main, text="合成预览区", bg="#f0f0f0", bd=1, relief=tk.SOLID)
        self.preview.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    def add_image(self):
        ps = filedialog.askopenfilenames(filetypes=[("PNG", "*.png")])
        for p in ps:
            if p not in self.image_paths:
                self.image_paths.append(p)
                self.listbox.insert(tk.END, os.path.basename(p))

    def clear_list(self):
        """清空当前的待合成列表"""
        self.image_paths = []
        self.listbox.delete(0, tk.END)
        self.preview.config(image="", text="列表已清空")
        self.result_img = None

    def run_logic(self):
        """逻辑：只要有白则为白 (OR 运算)"""
        if not self.image_paths: 
            messagebox.showwarning("提示", "请先添加至少一张分色图层")
            return
        
        # 将所有图片累加
        base = np.array(Image.open(self.image_paths[0]).convert("L"), dtype=np.uint32)
        for i in range(1, len(self.image_paths)):
            layer = np.array(Image.open(self.image_paths[i]).convert("L"), dtype=np.uint32)
            if layer.shape != base.shape:
                messagebox.showerror("错误", f"尺寸不匹配: {os.path.basename(self.image_paths[i])}")
                return
            base += layer
        
        # 大于0则设为白(255)，等于0保持黑(0)
        res_np = np.where(base > 0, 255, 0).astype(np.uint8)
        self.result_img = Image.fromarray(res_np)
        self.show_preview(self.result_img)

    def show_preview(self, img):
        self.update_idletasks()
        w, h = self.preview.winfo_width(), self.preview.winfo_height()
        if w < 10: w, h = 600, 400
        scale = min(w/img.size[0], h/img.size[1])
        resized = img.resize((int(img.size[0]*scale), int(img.size[1]*scale)), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized)
        self.preview.config(image=tk_img, text="")
        self.preview.image = tk_img

    def save_result(self):
        if self.result_img:
            p = filedialog.asksaveasfilename(defaultextension=".png")
            if p: self.result_img.save(p)

# ==========================================
# 主窗体：整合三个 Tab 页面
# ==========================================
class PCBMasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PCB 艺术加工一体化工作站 v1.1")
        self.root.geometry("1280x880")
        
        # 配置全局 Tab 样式
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=(get_main_font(), 10), padding=[12, 6])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 实例化三个功能模块
        self.tab1 = ColorMapperTab(self.notebook)
        self.tab2 = ColorSeparatorTab(self.notebook)
        self.tab3 = ImageLogicTab(self.notebook)

        # 添加到菜单
        self.notebook.add(self.tab1, text="  ① 色彩聚类映射  ")
        self.notebook.add(self.tab2, text="  ② 自动分色提取  ")
        self.notebook.add(self.tab3, text="  ③ 逻辑运算合成  ")

if __name__ == "__main__":
    root = tk.Tk()
    app = PCBMasterApp(root)
    
    # 全局滚轮绑定，方便滚动色卡列表
    def _on_mousewheel(event):
        # 仅在第一个标签页生效
        try:
            app.tab1.canvas_list.yview_scroll(int(-1*(event.delta/120)), "units")
        except: pass
    app.root.bind_all("<MouseWheel>", _on_mousewheel)
    
    root.mainloop()