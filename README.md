# PCB Art Workstation | PCB 艺术加工一体化工作站

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)

这是一个专为 **PCB 艺术设计** 打造的图像处理工具。它可以帮助你将普通的彩色图片转化为符合 PCB 生产工艺（如丝印、阻焊、铜箔层）的黑白分色图。
从 [Releases](../../releases) 页面下载最新版本的 `.exe` 文件，双击即可直接运行。使用方法见下文的功能模块介绍。

## 🌟 实物展示

<p align="center">
  <img width="40%" alt="案例green" src="https://github.com/user-attachments/assets/1c865312-a8c2-413d-bdde-96b294376377" />
</p>

<p align="center">
  <img width="40%" alt="案例blue" src="https://github.com/user-attachments/assets/a8b95dff-d71a-4a3a-83f4-839b2c12bdd4" />
</p>

## 🌟 功能模块介绍

本项目集成四个模块，构成完整的 PCB 图像处理流水线：

1.  **色彩聚类映射 (Color Mapping)**
    * 从原图直接点击吸色，选择有代表性的图片颜色。可以选1个最深色、1个最浅色、2个主体色，再选1个阴影深色和1个亮色，自由搭配。
    * 按照自定义色卡，将图片像素归类，生成色块分明的“艺术化”效果图。

<p align="center">
  <img width="60%" alt="UI预览1" src="https://github.com/user-attachments/assets/5ac30593-fdf3-40ae-9e05-b190f8a2d17b" />
</p>

2.  **自动分色提取 (Color Separation)**
    * 自动识别图片中的唯一颜色。
    * 一键将各颜色区域分离，生成独立的黑底白图。

<p align="center">
  <img width="60%" alt="UI预览2" src="https://github.com/user-attachments/assets/24cd04e4-7925-473d-afbb-1184740d3eb7" />
</p>

3.  **逻辑运算去噪 (Logic Synthesis)**
    * 支持多张黑白图层的合并运算，分别合成顶层丝印，顶层，顶层阻焊，底层，底层阻焊（Mask），直接对接 PCB 图层素材。
    * 遵循“全黑为黑，有白则白”的逻辑，并去除噪点。
    * 基本思路如下：丝印层包含白色；顶层包含白色，最深色；顶层阻焊包含较深的主体色，白色；底层包含最深色和阴影深色。

<p align="center">
  <img width="60%" alt="UI预览3" src="https://github.com/user-attachments/assets/d3f17f05-d6c5-4fc9-87a8-5f3f035f3310" />
</p>

4.  **添加宽度标记 (Add Width Anchors)**
    * 自动计算图片 1/100 宽度，在图片的左上角和右上角生成三角形锚点，专门解决 EDA 导入对齐问题。
    * 通过pcb板框倒角可以自动隐藏标记，不影响美观。
    * 锚点宽度可自行调整，图片插入立创EDA时使用反相。

<p align="center">
  <img width="60%" alt="UI预览4" src="https://github.com/user-attachments/assets/61000cd8-0bb3-42da-ba8c-a03a4ea1720c" />
</p>
