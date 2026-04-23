import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont

from src.lib.multi_condition_clean.EntireCompareTree.ab import Node


# --- 樹狀圖視覺化工具 ---
def tree_depth(node: Node) -> int:
    """計算樹的深度。"""
    if not node or not node.children:
        return 1
    return 1 + max(tree_depth(child) for child in node.children)


def tree_width(node: Node) -> int:
    """計算樹的視覺化寬度（簡化版）。"""
    if not node or not node.children:
        return 1
    return sum(tree_width(child) for child in node.children) if node.children else 1


class TreeVisualizer(tk.Toplevel):
    def __init__(self, master, root_node, title="規則樹視覺化工具", debug_mode=False):
        super().__init__(master)
        self.title(title)
        self.debug_mode = debug_mode
        self.root_node = root_node  # 儲存根節點，以便重繪

        # 初始畫布尺寸 (滾動區域會根據內容調整)
        self.initial_canvas_width = 900
        self.initial_canvas_height = 600

        # 節點間距設定
        self.node_spacing_x = 200  # 水平節點間距 (子樹間距)
        self.node_spacing_y = 180  # 垂直節點間距
        self.node_radius = 40  # 節點半徑

        # 創建控制按鈕框架
        control_frame = tk.Frame(self)
        control_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

        self.save_button = tk.Button(self, text="Save Image #2", command=self.save_image_with_pillow)
        self.save_button.grid(row=1, column=0, sticky="nsew", columnspan=2)  # 讓 Notebook 佔滿中間區域

        # 創建 Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=2, column=0, sticky="nsew", columnspan=2)  # 讓 Notebook 佔滿中間區域

        # 創建兩個分頁框架
        self.pre_exec_frame = ttk.Frame(self.notebook)
        self.post_exec_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.pre_exec_frame, text="執行前 (Pre-Execution)")
        self.notebook.add(self.post_exec_frame, text="執行後 (Post-Execution)")

        # 為每個分頁創建畫布和滾動條
        self.pre_exec_canvas, self.pre_exec_hbar, self.pre_exec_vbar = self._create_canvas_with_scrollbars(
            self.pre_exec_frame)
        self.post_exec_canvas, self.post_exec_hbar, self.post_exec_vbar = self._create_canvas_with_scrollbars(
            self.post_exec_frame)

        # 配置 grid 權重，確保 Notebook 在視窗大小改變時能正確擴展
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)  # 滾動條列不需要太多權重

        # 首次繪製樹狀圖
        self._draw_trees()

    def _create_canvas_with_scrollbars(self, parent_frame: tk.Frame):
        """
        在給定的父框架中創建一個 Canvas 和其對應的滾動條。
        """
        canvas = tk.Canvas(parent_frame, width=self.initial_canvas_width, height=self.initial_canvas_height, bg='white')
        canvas.grid(row=0, column=0, sticky="nsew")

        hbar = tk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        hbar.grid(row=1, column=0, sticky="ew")

        vbar = tk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=canvas.yview)
        vbar.grid(row=0, column=1, sticky="ns")

        canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        # 綁定滑鼠滾輪事件到這個畫布
        canvas.bind("<MouseWheel>", self._on_mousewheel_vertical)
        canvas.bind("<Button-4>", self._on_mousewheel_vertical)
        canvas.bind("<Button-5>", self._on_mousewheel_vertical)
        canvas.bind("<Shift-MouseWheel>", self._on_mousewheel_horizontal)
        canvas.bind("<Shift-Button-4>", self._on_mousewheel_horizontal)
        canvas.bind("<Shift-Button-5>", self._on_mousewheel_horizontal)

        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)

        return canvas, hbar, vbar

    def _on_mousewheel_vertical(self, event):
        """處理垂直滾動"""
        # 獲取當前活躍的畫布
        current_canvas = self.notebook.nametowidget(self.notebook.select()).winfo_children()[0]
        if event.num == 5 or event.delta == -120:  # 滾輪向下或向右
            current_canvas.yview_scroll(1, "unit")
        elif event.num == 4 or event.delta == 120:  # 滾輪向上或向左
            current_canvas.yview_scroll(-1, "unit")

    def _on_mousewheel_horizontal(self, event):
        """處理水平滾動 (按住 Shift 鍵)"""
        # 獲取當前活躍的畫布
        current_canvas = self.notebook.nametowidget(self.notebook.select()).winfo_children()[0]
        if event.num == 5 or event.delta == -120:  # 滾輪向下或向右
            current_canvas.xview_scroll(1, "unit")
        elif event.num == 4 or event.delta == 120:  # 滾輪向上或向左
            current_canvas.xview_scroll(-1, "unit")

    def _draw_trees(self):
        """
        繪製執行前和執行後的樹狀圖。
        """
        # 繪製執行前樹狀圖 (不顯示執行數據)
        self._draw_tree_on_canvas(self.pre_exec_canvas, self.root_node, show_execution_details=False)

        # 繪製執行後樹狀圖 (顯示執行數據)
        self._draw_tree_on_canvas(self.post_exec_canvas, self.root_node, show_execution_details=True)

    def _draw_tree_on_canvas(self, canvas: tk.Canvas, root_node: Node, show_execution_details: bool):
        """
        清除給定畫布，重新繪製樹狀圖，並根據內容設定滾動區域。
        """
        canvas.delete("all")  # 清除所有現有繪圖

        total_drawing_width_needed = self._calculate_subtree_drawing_width(root_node)
        depth = tree_depth(root_node)
        drawing_height = max(self.initial_canvas_height, depth * self.node_spacing_y + 200)

        canvas_width = max(self.initial_canvas_width, int(total_drawing_width_needed + self.node_radius * 4))

        self.draw_tree_recursive(root_node, canvas_width // 2, 50, total_drawing_width_needed, canvas, show_execution_details)

        bbox = canvas.bbox("all")
        if bbox:
            canvas.config(scrollregion=bbox)
            canvas.xview_moveto(0)
            canvas.yview_moveto(0)
        else:
            canvas.config(scrollregion=(0, 0, self.initial_canvas_width, self.initial_canvas_height))

    def _calculate_subtree_drawing_width(self, node: Node) -> float:
        """
        遞迴計算一個節點及其所有子節點在繪圖時所需的總水平寬度。
        考慮節點半徑和節點間距。
        """
        if not node:
            return 0.0
        if not node._children:
            return float(self.node_radius * 2)  # 葉節點的寬度就是其直徑

        # 子節點所需的總寬度
        children_total_width = 0.0
        for child in node._children:
            children_total_width += self._calculate_subtree_drawing_width(child)

        # 加上子節點之間的間距
        if len(node._children) > 1:
            children_total_width += (len(node._children) - 1) * self.node_spacing_x

        # 確保當前節點的寬度至少是其直徑，並取子節點總寬度與自身直徑的最大值
        return max(children_total_width, float(self.node_radius * 2))

    def draw_tree_recursive(self, node: Node, x: float, y: float, subtree_width_for_children_placement: float, canvas: tk.Canvas, show_execution_details: bool):
        """
        遞迴函數，用於繪製樹狀圖的節點和連線。
        """
        if node is None:
            return

        node_color = 'orange' if node.node_type == "Logic" else "red" if node.node_type == "SpecialOperator" else "lightblue"
        # canvas.create_rectangle(
        canvas.create_oval(
            x - self.node_radius, y - self.node_radius,
            x + self.node_radius, y + self.node_radius,
            fill=node_color, outline='black'
        )
        canvas.create_text(x, y, text=node.display_value, font=('Arial', 9), width=self.node_radius * 1.8)

        # 繪製執行後的詳細資訊
        if show_execution_details and node.result is not None:
            detail_text = ""
            if node.node_type == "Comparison":  # 比較節點顯示輸入數據
                df1_col = getattr(node.strategy, 'df1_col', 'N/A')
                df2_col = getattr(node.strategy, 'df2_col', 'N/A')
                val1 = node.last_executed_context.row1.get(df1_col, 'N/A')
                val2 = node.last_executed_context.row2.get(df2_col, 'N/A')
                detail_text += f"df1[{df1_col}]: {val1}\ndf2[{df2_col}]: {val2}\n"
            elif node.node_type == "SpecialOperator":  # 比較節點顯示輸入數據
                df1_col = getattr(node.strategy, 'df1_col', 'N/A')
                # df2_ac_col = getattr(node.strategy, 'df2_ac_col', 'N/A')
                # df2_constraint_col = getattr(node.strategy, 'df2_constraint_col', 'N/A')
                df2_ac_col = "AC"
                df2_constraint_col = "CONSTRAINTS"
                val1 = node.last_executed_context.source_row.get(df1_col, 'N/A')
                val2 = node.last_executed_context.root_node.get('right', 'N/A')
                val3 = node.last_executed_context.root_node.get('left', 'N/A')
                # val2 = node.last_executed_context.ac_table_row.get(df2_ac_col, 'N/A')
                # val3 = node.last_executed_context.ac_table_row.get(df2_constraint_col, 'N/A')
                detail_text += f"df1[{df1_col}]: {val1}\n"
                detail_text += f"df2[{df2_ac_col}]: {val2}\n"
                detail_text += f"df2[{df2_constraint_col}]: {val3}\n"

            detail_text += f"Result: {node.result}"

            # 調整文字位置，使其在節點右下方，避免重疊
            canvas.create_text(
                x + self.node_radius + 5,  # 稍微偏右
                y + self.node_radius + 5,  # 稍微偏下
                text=detail_text,
                anchor="nw",  # 左上角對齊
                font=('Arial', 7),
                fill='darkgreen' if node.result else 'darkred',
                width=self.node_radius * 2  # 確保文字可以換行
            )

        num_children = len(node.children)
        if num_children > 0:
            # 計算所有子節點（包括它們的子樹）所需的總水平寬度
            children_total_drawing_width = 0.0
            for child in node.children:
                children_total_drawing_width += self._calculate_subtree_drawing_width(child)
            if num_children > 1:
                children_total_drawing_width += (num_children - 1) * self.node_spacing_x

            # 確定第一個子節點的起始 x 座標，以便將所有子節點組居中在父節點下方
            current_x_position_for_child = x - children_total_drawing_width / 2

            for i, child in enumerate(node.children):
                child_drawing_width = self._calculate_subtree_drawing_width(child)

                # 新的子節點 x 座標是其子樹的中心點
                new_x = current_x_position_for_child + child_drawing_width / 2
                new_y = y + self.node_spacing_y  # 垂直向下移動

                canvas.create_line(x, y + self.node_radius, new_x, new_y - self.node_radius)

                # 遞迴繪製子節點，並將該子節點的子樹繪圖寬度傳遞給它，用於其子節點的定位
                self.draw_tree_recursive(child, new_x, new_y, child_drawing_width, canvas, show_execution_details)

                # 移動到下一個子節點的起始位置
                current_x_position_for_child += child_drawing_width + self.node_spacing_x

    def save_image_with_pillow(self, scale=2):
        """
            真的是有夠誇張 !!!?
            tkinter 提供 canvas 卻無法提供 canvas 直接轉成圖片的功能
            1. 大部分人就直接採用 Pillow ImageGrab 的 螢幕截圖方式，但因為本突有摺疊部分，螢幕截圖基本上很難用(幾乎無法)
            2. 剩餘部份的人就會去下載所謂 GhostScript 套件，然後把 canvas.info 轉換成 .ps 再用套件轉換成 .png。然後，
                (1) 路徑問題 與 引用 再venv 裡面有夠麻煩
                (2) 用完以後，又因為所謂字體、顏色、或是其他設定不同，的未知原因直接導致畫出來的只有一張小白方塊圖，我真的要氣死
            3. 無可奈何之下，重寫一次畫樹的算法，並增加解析度就輸出了
        """
        """用 Pillow 繪製並保存高解析度圖片。"""
        try:
            from PIL import ImageFont

            # 放大字型大小
            base_font_size = 12 * scale
            base_font_small_size = 9 * scale

            font = ImageFont.truetype("arial.ttf", base_font_size)
            font_small = ImageFont.truetype("arial.ttf", base_font_small_size)

            width = max(self.initial_canvas_width, int(self._calculate_subtree_drawing_width(self.root_node) + self.node_radius * 4))
            depth = tree_depth(self.root_node)
            height = max(self.initial_canvas_height, depth * self.node_spacing_y + 200)

            # 放大尺寸
            width *= scale
            height *= scale
            node_radius = self.node_radius * scale
            node_spacing_x = self.node_spacing_x * scale
            node_spacing_y = self.node_spacing_y * scale

            img = Image.new("RGBA", (int(width), int(height)), "white")
            draw = ImageDraw.Draw(img)

            def draw_node(node, x, y, subtree_width):
                if node is None:
                    return

                node_color = (255, 165, 0, 255) if node.node_type == "Operator" else (173, 216, 230, 255)

                bbox = [x - node_radius, y - node_radius, x + node_radius, y + node_radius]
                draw.ellipse(bbox, fill=node_color, outline="black")

                max_width = node_radius * 1.8
                words = node.display_value.split()
                lines = []
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    bbox_text = draw.textbbox((0, 0), test_line, font=font)
                    w = bbox_text[2] - bbox_text[0]
                    if w <= max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)

                bbox_line = draw.textbbox((0, 0), "A", font=font)
                line_height = bbox_line[3] - bbox_line[1]
                total_text_height = line_height * len(lines)
                text_y = y - total_text_height / 2

                for line in lines:
                    bbox_line = draw.textbbox((0, 0), line, font=font)
                    w = bbox_line[2] - bbox_line[0]
                    draw.text((x - w / 2, text_y), line, fill="black", font=font)
                    text_y += line_height

                if hasattr(node, '_last_executed_context') and node.last_executed_context is not None:
                    detail_text = ""
                    if node.node_type == "Comparison":
                        df1_col = getattr(node.strategy, 'df1_col', 'N/A')
                        df2_col = getattr(node.strategy, 'df2_col', 'N/A')
                        val1 = node.last_executed_context.row1.get(df1_col, 'N/A')
                        val2 = node.last_executed_context.row2.get(df2_col, 'N/A')
                        detail_text += f"df1[{df1_col}]: {val1}\ndf2[{df2_col}]: {val2}\n"
                    detail_text += f"Result: {node.last_execution_result}"

                    fill_color = (0, 100, 0, 255) if node.last_execution_result else (139, 0, 0, 255)
                    detail_lines = detail_text.split('\n')
                    text_x = x + node_radius + 5
                    text_y = y + node_radius + 5
                    for line in detail_lines:
                        bbox_detail = draw.textbbox((0, 0), line, font=font_small)
                        h = bbox_detail[3] - bbox_detail[1]
                        draw.text((text_x, text_y), line, fill=fill_color, font=font_small)
                        text_y += h

                num_children = len(node.children)
                if num_children > 0:
                    children_total_width = 0.0
                    for child in node.children:
                        children_total_width += self._calculate_subtree_drawing_width(child) * scale
                    if num_children > 1:
                        children_total_width += (num_children - 1) * node_spacing_x

                    current_x = x - children_total_width / 2

                    for child in node.children:
                        child_width = self._calculate_subtree_drawing_width(child) * scale
                        new_x = current_x + child_width / 2
                        new_y = y + node_spacing_y

                        draw.line((x, y + node_radius, new_x, new_y - node_radius), fill="black")

                        draw_node(child, new_x, new_y, child_width)
                        current_x += child_width + node_spacing_x

            draw_node(self.root_node, width // 2, 50 * scale,
                      self._calculate_subtree_drawing_width(self.root_node) * scale)

            path_ = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if path_:
                img.save(path_)
                messagebox.showinfo("Success", f"Saved high-res image to {path_}")

        except Exception as e:
            print(f"Failed to save high-res image with Pillow: {e}")
            messagebox.showerror("Error", f"Failed to save high-res image with Pillow: {e}")





