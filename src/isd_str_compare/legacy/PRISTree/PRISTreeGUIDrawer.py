import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont

from src.lib.multi_condition_clean.PRISTree.PRISTreeNodeBase import tree_depth, tree_width


# GUI 類別：繪製樹狀結構視窗
class TreeVisualizer(tk.Toplevel):
    def __init__(self, master, root_node, title="Binary Tree Viewer", debug_mode=False):
        super().__init__(master)
        self.title(title)
        self.root_node = root_node  # 儲存根節點，以便後續操作
        self.debug_mode = debug_mode

        # 初始設定
        self.initial_canvas_width = 900
        self.initial_canvas_height = 600
        self.node_spacing_x = 100
        self.node_spacing_y = 120
        self.node_radius = 30

        # --- 新增的控制按鈕與 Notebook ---
        self.save_button = tk.Button(self, text="Save Image", command=self.save_image_with_pillow)
        self.save_button.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.tree_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tree_frame, text="二元樹視覺化")

        # --- 使用封裝函式建立畫布與滾動條 ---
        self.canvas, self.hbar, self.vbar = self._create_canvas_with_scrollbars(self.tree_frame)

        # 繪製樹狀圖
        self._draw_tree()

    def _create_canvas_with_scrollbars(self, parent_frame: tk.Frame):
        canvas = tk.Canvas(parent_frame, width=self.initial_canvas_width, height=self.initial_canvas_height, bg='white')
        canvas.grid(row=0, column=0, sticky="nsew")

        hbar = tk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        hbar.grid(row=1, column=0, sticky="ew")

        vbar = tk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=canvas.yview)
        vbar.grid(row=0, column=1, sticky="ns")

        canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        # 綁定滑鼠滾輪事件
        canvas.bind("<MouseWheel>", lambda event: canvas.yview_scroll(-1 * (event.delta // 120), "units"))
        canvas.bind("<Shift-MouseWheel>", lambda event: canvas.xview_scroll(-1 * (event.delta // 120), "units"))

        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)

        return canvas, hbar, vbar

    def _draw_tree(self):
        """
        清除畫布並重新繪製樹狀圖，同時調整滾動區域。
        """
        self.canvas.delete("all")
        depth = tree_depth(self.root_node)
        width_nodes = tree_width(self.root_node)

        # 動態計算畫布寬度與高度
        canvas_width = max(self.initial_canvas_width, width_nodes * self.node_spacing_x + 200)
        canvas_height = max(self.initial_canvas_height, depth * self.node_spacing_y + 200)

        # 重新配置滾動區域
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

        # 核心繪圖邏輯
        self.draw_tree_recursive(self.root_node, canvas_width // 2, 50, canvas_width // 4)

    # 你的原有 draw_tree 方法需要修改為遞迴模式
    def draw_tree_recursive(self, node, x, y, x_offset):
        if node is None:
            return

        # 畫節點圓與文字
        node_color = 'lightblue' if node.node_type == "AC" else "orange" if node.node_type == "LOGIC" else "red"
        self.canvas.create_oval(
            x - self.node_radius, y - self.node_radius,
            x + self.node_radius, y + self.node_radius,
            fill=node_color, outline='black'
        )
        self.canvas.create_text(x, y, text=node.value, font=('Arial', 10), width=self.node_radius * 2)

        if self.debug_mode:
            print(f"[DEBUG] Drawing node '{node.value}' at ({x},{y})")

        # 繪製左子節點及連線
        if node.left:
            new_x = x - x_offset
            new_y = y + self.node_spacing_y
            self.canvas.create_line(x, y + self.node_radius, new_x, new_y - self.node_radius)
            if self.debug_mode:
                print(f"[DEBUG] Drawing left child of '{node.value}'")
            self.draw_tree_recursive(node.left, new_x, new_y, max(x_offset // 2, 20))

        # 繪製右子節點及連線
        if node.right:
            new_x = x + x_offset
            new_y = y + self.node_spacing_y
            self.canvas.create_line(x, y + self.node_radius, new_x, new_y - self.node_radius)
            if self.debug_mode:
                print(f"[DEBUG] Drawing right child of '{node.value}'")
            self.draw_tree_recursive(node.right, new_x, new_y, max(x_offset // 2, 20))

    # 這是你需要新增到 TreeVisualizer 類別中的方法
    def save_image_with_pillow(self, scale=2):
        try:
            # 計算所需的圖片尺寸
            depth = tree_depth(self.root_node)
            width_nodes = tree_width(self.root_node)

            width = max(self.initial_canvas_width, width_nodes * self.node_spacing_x + 200)
            height = max(self.initial_canvas_height, depth * self.node_spacing_y + 200)

            width *= scale
            height *= scale
            node_radius = self.node_radius * scale
            node_spacing_x = self.node_spacing_x * scale
            node_spacing_y = self.node_spacing_y * scale

            img = Image.new("RGBA", (int(width), int(height)), "white")
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("arial.ttf", 10 * scale)

            def draw_node_recursive_for_pillow(node, x, y, x_offset):
                if node is None:
                    return

                node_color = (173, 216, 230, 255) if node.node_type == "AC" else (
                255, 165, 0, 255) if node.node_type == "LOGIC" else (255, 0, 0, 255)
                bbox = [x - node_radius, y - node_radius, x + node_radius, y + node_radius]
                draw.ellipse(bbox, fill=node_color, outline="black")

                # --- 修正後的文字繪製邏輯 ---
                text_content = node.value
                # 使用 textbbox 獲取文字的邊界框
                # 注意：textbbox 的坐標是相對於文字左上角，而不是中心
                left, top, right, bottom = draw.textbbox((0, 0), text_content, font=font)
                text_width = right - left
                text_height = bottom - top

                # 調整文字位置，使其在圓心
                draw.text(
                    (x - text_width / 2, y - text_height / 2),
                    text_content,
                    fill="black",
                    font=font
                )

                # 繪製左子節點及連線
                if node.left:
                    new_x = x - x_offset
                    new_y = y + node_spacing_y
                    draw.line((x, y + node_radius, new_x, new_y - node_radius), fill="black")
                    draw_node_recursive_for_pillow(node.left, new_x, new_y, max(x_offset // 2, 20 * scale))

                # 繪製右子節點及連線
                if node.right:
                    new_x = x + x_offset
                    new_y = y + node_spacing_y
                    draw.line((x, y + node_radius, new_x, new_y - node_radius), fill="black")
                    draw_node_recursive_for_pillow(node.right, new_x, new_y, max(x_offset // 2, 20 * scale))

            draw_node_recursive_for_pillow(self.root_node, width // 2, 50 * scale, width // 4)

            path_ = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if path_:
                img.save(path_)
                messagebox.showinfo("Success", f"Saved high-res image to {path_}")

        except Exception as e:
            print(f"Failed to save high-res image with Pillow: {e}")
            messagebox.showerror("Error", f"Failed to save high-res image with Pillow: {e}")

