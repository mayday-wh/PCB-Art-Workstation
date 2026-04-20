# PCB Art Workstation | PCB 艺术加工一体化工作站

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)

这是一个专为 **PCB 艺术设计** 打造的图像处理工具。它可以帮助你将普通的彩色图片转化为符合 PCB 生产工艺（如丝印、阻焊、铜箔层）的黑白分色图。

## 🌟 核心功能

本项目集成三大核心模块，构成完整的 PCB 图像处理流水线：

1.  **色彩聚类映射 (Color Mapping)**
    * 支持从原图直接点击吸色。
    * 按照自定义色卡，将图片像素归类，生成色块分明的“艺术化”效果图。
    * 支持颜色方案（JSON）的导入与导出。
    * 
<img width="2564" height="1824" alt="1979" src="https://github.com/user-attachments/assets/2ffb930d-2734-40f3-ba2c-de8a7449a164" />

2.  **自动分色提取 (Color Separation)**
    * 自动识别图片中的唯一颜色。
    * 一键将各颜色区域分离，生成独立的黑底白图（Mask），直接对接 PCB 图层素材。
3.  **逻辑运算合成 (Logic Synthesis)**
    * 支持多张黑白图层的合并运算。
    * 遵循“全黑为黑，有白则白”的逻辑，方便将多个工艺层合并。

## 🛠️ 安装与运行

### 方式一：直接运行（推荐）
从 [Releases](../../releases) 页面下载最新版本的 `.exe` 文件，双击即可直接运行。

### 方式二：源码运行
如果你想参与开发，请确保已安装 Python 环境：

1. 克隆项目：
   ```bash
   git clone [https://github.com/mayday-wh/PCB-Art-Workstation.git](https://github.com/mayday-wh/PCB-Art-Workstation.git)
