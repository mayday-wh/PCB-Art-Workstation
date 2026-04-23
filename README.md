# PCB Art Workstation | PCB 艺术加工一体化工作站

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)

这是一个专为 **PCB 艺术设计** 打造的图像处理工具。它可以帮助你将普通的彩色图片转化为符合 PCB 生产工艺（如丝印、阻焊、铜箔层）的黑白分色图。
从 [Releases](../../releases) 页面下载最新版本的 `.exe` 文件，双击即可直接运行。

## 🌟 功能模块介绍

本项目集成三个模块，构成完整的 PCB 图像处理流水线：

1.  **色彩聚类映射 (Color Mapping)**
    * 从原图直接点击吸色，选择有代表性的图片颜色。
    * 按照自定义色卡，将图片像素归类，生成色块分明的“艺术化”效果图。

<p align="center">
  <img width="60%" alt="UI预览1" src="https://github.com/user-attachments/assets/460ea277-151c-4d44-8efb-00f76d381d9f" />
</p>

2.  **自动分色提取 (Color Separation)**
    * 自动识别图片中的唯一颜色。
    * 一键将各颜色区域分离，生成独立的黑底白图。

<p align="center">
  <img width="60%" alt="UI预览2" src="https://github.com/user-attachments/assets/e0632e5c-d340-4aec-92bf-82c78312d034" />
</p>

3.  **逻辑运算去噪 (Logic Synthesis)**
    * 支持多张黑白图层的合并运算，分别合成顶层丝印，顶层，顶层阻焊，底层，底层阻焊（Mask），直接对接 PCB 图层素材。。
    * 遵循“全黑为黑，有白则白”的逻辑，并去除噪点。

<p align="center">
  <img width="60%" alt="UI预览3" src="https://github.com/user-attachments/assets/b9ee893a-7fdf-4454-a134-bf7859659223" />
</p>
