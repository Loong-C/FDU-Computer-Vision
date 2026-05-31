#!/usr/bin/env python3
"""Generate the Task 1 PDF report from tracked data and local report assets."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "report"
ASSET_DIR = REPORT_DIR / "assets"
DATA_PATH = REPORT_DIR / "report_data.json"


def register_fonts() -> None:
    font_dir = Path("/mnt/c/Windows/Fonts")
    pdfmetrics.registerFont(TTFont("SimHei", str(font_dir / "simhei.ttf")))
    pdfmetrics.registerFont(TTFont("Arial", str(font_dir / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(font_dir / "arialbd.ttf")))


def build_styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCN",
            parent=sample["Title"],
            fontName="SimHei",
            fontSize=22,
            leading=32,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleCN",
            parent=sample["Normal"],
            fontName="SimHei",
            fontSize=12,
            leading=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#444444"),
        ),
        "h1": ParagraphStyle(
            "Heading1CN",
            parent=sample["Heading1"],
            fontName="SimHei",
            fontSize=15,
            leading=22,
            spaceBefore=12,
            spaceAfter=7,
            textColor=colors.HexColor("#17365D"),
        ),
        "h2": ParagraphStyle(
            "Heading2CN",
            parent=sample["Heading2"],
            fontName="SimHei",
            fontSize=12.5,
            leading=19,
            spaceBefore=9,
            spaceAfter=5,
            textColor=colors.HexColor("#244062"),
        ),
        "body": ParagraphStyle(
            "BodyCN",
            parent=sample["BodyText"],
            fontName="SimHei",
            fontSize=9.6,
            leading=16,
            alignment=TA_LEFT,
            spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "SmallCN",
            parent=sample["BodyText"],
            fontName="SimHei",
            fontSize=8.1,
            leading=12,
            alignment=TA_LEFT,
        ),
        "caption": ParagraphStyle(
            "CaptionCN",
            parent=sample["BodyText"],
            fontName="SimHei",
            fontSize=8.4,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"),
            spaceAfter=7,
        ),
        "table": ParagraphStyle(
            "TableCN",
            parent=sample["BodyText"],
            fontName="SimHei",
            fontSize=7.8,
            leading=11,
            alignment=TA_LEFT,
        ),
    }


def paragraph(text: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), style)


def section(story: list[object], styles: dict[str, ParagraphStyle], text: str) -> None:
    story.append(Paragraph(escape(text), styles["h1"]))


def subsection(story: list[object], styles: dict[str, ParagraphStyle], text: str) -> None:
    story.append(Paragraph(escape(text), styles["h2"]))


def add_table(
    story: list[object],
    styles: dict[str, ParagraphStyle],
    rows: list[list[object]],
    widths: list[float],
) -> None:
    table_rows = [
        [paragraph(cell, styles["table"]) for cell in row]
        for row in rows
    ]
    table = Table(table_rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17365D")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#A6A6A6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FBFD")]),
            ]
        )
    )
    story.extend([table, Spacer(1, 6)])


def add_image(
    story: list[object],
    styles: dict[str, ParagraphStyle],
    name: str,
    caption: str,
    max_width: float = 16.2 * cm,
    max_height: float = 10.3 * cm,
) -> None:
    path = ASSET_DIR / name
    if not path.exists():
        story.append(paragraph(f"[草稿占位] 尚未生成图片：{name}", styles["small"]))
        return
    with PILImage.open(path) as image:
        width, height = image.size
    scale = min(max_width / width, max_height / height)
    story.append(
        KeepTogether(
            [
                Image(str(path), width=width * scale, height=height * scale, hAlign="CENTER"),
                paragraph(caption, styles["caption"]),
            ]
        )
    )


def link_text(label: str, value: str) -> str:
    if value == "PENDING":
        return "PENDING"
    return f"{label}: {value}"


def require_final_deliverables(data: dict[str, object]) -> None:
    if data["status"] != "final":
        raise RuntimeError("Set report_data.json status to 'final' before publishing.")
    required = {
        "cloud_weights_url": data["cloud_weights_url"],
        "object_c.formal_mesh": data["object_c"]["formal_mesh"],
        "object_c.preview": data["object_c"]["preview"],
        "fusion.video": data["fusion"]["video"],
        "fusion.preview": data["fusion"]["preview"],
    }
    for label, value in required.items():
        if value in {None, "", "PENDING"}:
            raise RuntimeError(f"Missing final report field: {label}")
        if label != "cloud_weights_url" and not (ROOT / value).exists():
            raise FileNotFoundError(ROOT / value)
    for label in ["coarse_seconds", "fine_seconds"]:
        if data["object_c"][label] is None:
            raise RuntimeError(f"Missing final report field: object_c.{label}")
    if data["fusion"]["render_seconds"] is None:
        raise RuntimeError("Missing final report field: fusion.render_seconds")


def footer(canvas, document) -> None:  # noqa: ANN001
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#BFBFBF"))
    canvas.setLineWidth(0.4)
    canvas.line(2.2 * cm, 1.45 * cm, 18.8 * cm, 1.45 * cm)
    canvas.setFont("SimHei", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2.2 * cm, 1.05 * cm, "FDU Computer Vision HW3 - Task 1")
    canvas.drawRightString(18.8 * cm, 1.05 * cm, f"第 {document.page} 页")
    canvas.restoreState()


def make_story(data: dict[str, object], styles: dict[str, ParagraphStyle]) -> list[object]:
    story: list[object] = []
    draft = data["status"] != "final"
    title_suffix = "（草稿）" if draft else ""
    story.extend(
        [
            Spacer(1, 2.3 * cm),
            Paragraph(f"计算机视觉 HW3 题目一实验报告{title_suffix}", styles["title"]),
            Paragraph("基于 2DGS 与 AIGC 的多源资产生成与真实场景融合", styles["subtitle"]),
            Spacer(1, 1.0 * cm),
        ]
    )
    add_table(
        story,
        styles,
        [
            ["项目", "内容"],
            ["成员与分工", f"{data['student_name']}（{data['student_id']}），单人完成"],
            ["代码仓库", f"{data['github_url']}  分支：{data['github_branch']}"],
            ["模型权重", link_text("下载地址", data["cloud_weights_url"])],
            ["报告日期", data["generated_on"]],
        ],
        [3.2 * cm, 12.7 * cm],
    )
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        paragraph(
            "本报告对应期末作业题目一。目标是在同一流程中完成真实多视角重建、文本到 3D、"
            "单图到 3D、开源背景场景重建，以及统一表示下的场景融合与漫游渲染。",
            styles["body"],
        )
    )
    if draft:
        story.append(
            paragraph(
                "说明：当前 PDF 是可复现构建流程的草稿。Object C 正式结果、融合视频和云端权重链接"
                "尚未完成时，发布命令会主动拒绝生成正式版。",
                styles["body"],
            )
        )
    story.append(PageBreak())

    section(story, styles, "1. 任务背景与验收拆解")
    story.append(
        paragraph(
            "题目要求准备三个独立 3D 资产：物体 A 使用手机环绕拍摄、COLMAP 位姿估计和 "
            "2D Gaussian Splatting；物体 B 使用 threestudio 和 Stable Diffusion SDS，仅由文本 "
            "Prompt 生成；物体 C 使用单张手机实拍图，完成去背景后交给 Magic123。背景选择 "
            "Mip-NeRF 360 的 counter 场景并使用 2DGS 重建。最后将四类来源统一后在 Blender "
            "中组合，输出多视角漫游视频。",
            styles["body"],
        )
    )
    add_table(
        story,
        styles,
        [
            ["资产", "输入", "技术路线", "状态"],
            ["物体 A", "34 张手机多视角照片", "COLMAP + 2DGS + TSDF Mesh", "已完成"],
            ["物体 B", "1 条文本 Prompt", "threestudio DreamFusion + SD 1.5 SDS", "已完成"],
            ["物体 C", "1 张实拍图 c.png", "去背景 + MiDaS + Magic123 coarse/fine", "正式长跑中" if draft else "已完成"],
            ["背景", "Mip-NeRF 360 counter", "2DGS + TSDF Mesh", "已完成"],
            ["融合", "A/B/C + 背景 Mesh", "Blender 统一坐标系与环绕相机", "待正式 C 完成" if draft else "已完成"],
        ],
        [2.1 * cm, 4.0 * cm, 6.8 * cm, 3.0 * cm],
    )

    section(story, styles, "2. 数据集与准备过程")
    add_table(
        story,
        styles,
        [
            ["资产", "来源与规模", "准备步骤"],
            ["物体 A", "手机环绕拍摄，34 / 34 张注册", "COLMAP 特征、匹配、稀疏重建、去畸变"],
            ["物体 B", "文本 Prompt 1 条", "固定产品摄影描述，直接驱动 SDS 优化"],
            ["物体 C", "桌面 c.png，1448 × 1086", "棋盘格去背景、RGBA Alpha、MiDaS 深度"],
            ["背景", "Mip-NeRF 360 counter，240 张", "选择性下载开源场景并复用相机参数"],
        ],
        [2.1 * cm, 5.2 * cm, 8.6 * cm],
    )
    story.append(
        paragraph(
            "物体 A 的 COLMAP 稀疏模型注册 34 / 34 张图像，得到 1527 个稀疏点和 5203 次观测；"
            "平均轨迹长度为 3.407335，平均每图观测数为 153.029412，平均重投影误差为 "
            "1.192686 像素。该结果说明手机采集序列具有足够的视角重叠，可继续进入 2DGS 优化。",
            styles["body"],
        )
    )
    add_image(story, styles, "asset_preview_montage.jpg", "图 1：当前可用资产与背景预览。")

    section(story, styles, "3. 方法")
    subsection(story, styles, "3.1 物体 A 与背景：COLMAP / 2DGS")
    story.append(
        paragraph(
            "物体 A 先由 COLMAP 恢复相机位姿和稀疏点云，再交给官方 2DGS 实现训练。背景 counter "
            "使用开源数据自带的多视角图像。2DGS 使用显式二维高斯面片表示表面，并结合几何正则项。"
            "训练后分别导出渲染图，并使用有界 TSDF 参数提取 Mesh，避免默认参数超出本机 WSL 内存。",
            styles["body"],
        )
    )
    subsection(story, styles, "3.2 物体 B：DreamFusion SDS")
    story.append(
        paragraph(
            "物体 B 的 Prompt 为：A studio product photo of a small red ceramic teapot with a round "
            "body, short spout, and curved handle。threestudio 使用公共 Stable Diffusion 1.5 模型，"
            "在随机视角渲染结果上计算 SDS Loss，并在 10000 次迭代后导出带纹理 OBJ。",
            styles["body"],
        )
    )
    subsection(story, styles, "3.3 物体 C：Magic123")
    story.append(
        paragraph(
            "物体 C 的 Prompt 为：A high-resolution DSLR product photo of an amoxicillin capsule "
            "medicine box。预处理将桌面棋盘格背景移除，得到 RGBA 前景，并由 MiDaS 估计深度。"
            "Magic123 coarse 阶段同时使用 SD 1.5 与 Zero123 先验优化 NeRF；fine 阶段从 coarse "
            "检查点初始化 DMTet Mesh 并继续细化。",
            styles["body"],
        )
    )
    subsection(story, styles, "3.4 统一表示与融合")
    story.append(
        paragraph(
            "不同路线的原生输出不一致：2DGS 是显式高斯面片，AIGC 路线通常输出隐式场或 Mesh。"
            "本实验选择带颜色或纹理的 Mesh 作为交换表示：A 与背景由 2DGS 表面提取，B 与 C "
            "由生成框架导出 OBJ。随后在 Blender 中统一比例、位置、坐标轴和相机轨迹，渲染漫游视频。",
            styles["body"],
        )
    )

    section(story, styles, "4. 超参数与实现细节")
    add_table(
        story,
        styles,
        [
            ["阶段", "迭代 / 分辨率", "优化器与关键参数", "主要指标"],
            ["物体 A 2DGS", "30000 / 原始尺寸", "lambda_normal=0.05，lambda_dist=0，depth_ratio=0", "PSNR，L1，点数"],
            ["背景 2DGS", "30000 / half", "lambda_normal=0.05，lambda_dist=0，depth_ratio=0", "PSNR，L1，点数"],
            ["物体 B DreamFusion", "10000 / 64 × 64", "Adam，SD 1.5 SDS，guidance_scale=100", "SDS Loss，Mesh"],
            ["物体 C coarse", "500 local / 128 × 128", "Adam，SD + Zero123，lambda_guidance=[1.0, 40]", "总 Loss，各引导项"],
            ["物体 C fine", "500 local / DMTet", "Adam，SD + Zero123，lambda_guidance=[1e-3, 0.01]", "总 Loss，Mesh"],
        ],
        [2.5 * cm, 3.0 * cm, 7.5 * cm, 2.9 * cm],
    )
    story.append(
        paragraph(
            "所有长跑通过 tracked wrapper 启动：终端输出写入 logs/，TensorBoard 标量被导入 SwanLab "
            "local runs，并在阶段结束时写出 JSON 元数据。Magic123 同时加载 Stable Diffusion 和 "
            "Zero123，本机将 WSL 内存调整为 26 GB，并将 32 GB swap、模型缓存和 CLIP 缓存放在 D 盘。",
            styles["body"],
        )
    )

    section(story, styles, "5. 实验结果")
    subsection(story, styles, "5.1 物体 A 与背景的 2DGS 评估")
    add_table(
        story,
        styles,
        [
            ["资产", "迭代", "PSNR (dB)", "L1", "高斯点数", "Patch Total Loss"],
            ["物体 A", "7000", "31.8275", "0.015616", "149488", "未在该事件保留"],
            ["物体 A", "30000", "33.5198", "0.011289", "212465", "0.027321"],
            ["counter 背景", "7000", "28.0689", "0.021551", "482345", "未在该事件保留"],
            ["counter 背景", "30000", "29.9138", "0.016986", "533358", "0.024275"],
        ],
        [2.8 * cm, 1.7 * cm, 2.4 * cm, 2.2 * cm, 2.2 * cm, 4.6 * cm],
    )
    add_image(story, styles, "2dgs_validation_metrics.png", "图 2：物体 A 与 counter 背景的 2DGS 验证曲线。")
    subsection(story, styles, "5.2 物体 B 文本到 3D")
    story.append(
        paragraph(
            "DreamFusion 正式训练在 3624.22 秒内完成 10000 步，随后用 35.46 秒导出 OBJ。最终网格"
            "包含 28180 个顶点和 56536 个三角面。预览中可辨认红色陶瓷茶壶的壶盖、短壶嘴、圆形壶身"
            "和弯曲把手。SDS Loss 本身具有较强随机性，因此图中同时展示原始序列与移动平均。",
            styles["body"],
        )
    )
    add_image(story, styles, "object_b_sds_curve.png", "图 3：物体 B 的 DreamFusion SDS 优化曲线。")
    subsection(story, styles, "5.3 物体 C 单图到 3D")
    if draft:
        story.append(
            paragraph(
                "Magic123 coarse 与 fine smoke 均已通过：coarse smoke 为 285.69 秒，fine smoke 为 "
                "194.61 秒，并成功导出 OBJ。正式本地 500 + 500 步队列正在运行；官方参考预算为 "
                "5000 + 5000 步。本草稿保留动态曲线，正式版将在队列完成后写入最终 Mesh、预览和精确耗时。",
                styles["body"],
            )
        )
    else:
        total_c = data["object_c"]["coarse_seconds"] + data["object_c"]["fine_seconds"]
        story.append(
            paragraph(
                f"Magic123 正式 coarse 与 fine 阶段均已完成，总耗时为 {total_c:.2f} 秒。"
                f"最终网格位于 {data['object_c']['formal_mesh']}。",
                styles["body"],
            )
        )
    add_image(story, styles, "object_c_magic123_losses.png", "图 4：物体 C Magic123 正式队列的动态 Loss 曲线。")
    subsection(story, styles, "5.4 融合场景与漫游")
    if draft:
        story.append(
            paragraph(
                "融合脚本与 Blender 4.2.15 LTS 运行时已经准备完毕。正式物体 C OBJ 生成后，队列将"
                "导入四类 Mesh、应用 configs/fusion_scene.json 中的变换，并渲染环绕漫游视频。",
                styles["body"],
            )
        )
    else:
        story.append(
            paragraph(
                f"融合视频位于 {data['fusion']['video']}，渲染耗时为 "
                f"{data['fusion']['render_seconds']:.2f} 秒。",
                styles["body"],
            )
        )
        add_image(story, styles, "fusion_walkthrough_preview.png", "图 5：最终融合场景漫游视频代表帧。")
    add_image(story, styles, "runtime_comparison.png", "图 6：已完成正式阶段的端到端耗时比较。")

    section(story, styles, "6. 对比分析")
    add_table(
        story,
        styles,
        [
            ["路线", "几何准确性", "纹理细节", "输入成本", "计算与失败模式"],
            ["多视角重建", "真实观测充分时最佳，可量化 PSNR", "保留实拍细节较好", "需拍摄环绕序列并恢复位姿", "COLMAP 对纹理和重叠敏感；2DGS 训练稳定"],
            ["文本到 3D", "可生成清晰类别轮廓，但局部结构会受先验偏差影响", "外观可控但未必符合真实对象", "仅需 Prompt，最低", "SDS 随机性较强，需较长优化和预览筛查"],
            ["单图到 3D", "正面受真实图约束，背面依赖先验补全", "正面纹理可保留，侧后面较不确定", "单图与去背景，居中", "SD + Zero123 同载入造成主存压力，需显式内存管理"],
        ],
        [2.4 * cm, 4.1 * cm, 3.7 * cm, 2.8 * cm, 4.1 * cm],
    )
    story.append(
        paragraph(
            "三条路线形成互补：多视角重建最适合已有真实对象且能够拍摄充分视角的情况；文本到 3D "
            "适合快速生成虚拟资产；单图到 3D 在输入成本与真实纹理保持之间折中。统一为 Mesh 后，"
            "Blender 可直接承担尺度调整、遮挡关系和漫游渲染。",
            styles["body"],
        )
    )

    section(story, styles, "7. SwanLab 实验管理与可复现性")
    story.append(
        paragraph(
            "本仓库使用 SwanLab local mode 统一管理实验。2DGS wrapper 导入官方 TensorBoard 标量；"
            "DreamFusion wrapper 在结束时递归导入 TensorBoard；Magic123 wrapper 同时解析终端步骤"
            "并保留 TensorBoard。非训练事件，例如 COLMAP、缓存迁移、OOM 诊断和队列恢复，则使用"
            "独立 milestone logger 记录。以下曲线由相同本地标量导出，可与 SwanLab dashboard 对照。",
            styles["body"],
        )
    )
    add_image(story, styles, "2dgs_validation_metrics.png", "图 7：SwanLab 对应的 2DGS 验证指标。")
    add_image(story, styles, "object_b_sds_curve.png", "图 8：SwanLab 对应的 DreamFusion SDS 指标。")
    add_image(story, styles, "object_c_magic123_losses.png", "图 9：SwanLab 对应的 Magic123 动态指标。")
    story.append(
        paragraph(
            "本地看板命令：swanlab watch hw3/task1/swanlog。训练、测试、网格导出、Blender 融合命令"
            "均列在 hw3/task1/README.md 中；环境依赖列在 requirements.txt、environment.yml 和两个"
            "兼容性 requirements 文件中。",
            styles["body"],
        )
    )

    story.append(PageBreak())
    section(story, styles, "8. 外部链接")
    add_table(
        story,
        styles,
        [
            ["项目", "链接 / 说明"],
            ["Public GitHub Repository", f"{data['github_url']}  (branch: {data['github_branch']})"],
            ["模型权重下载", data["cloud_weights_url"]],
            ["融合视频", data["fusion"]["video"]],
        ],
        [4.0 * cm, 11.9 * cm],
    )
    return story


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    register_fonts()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if args.final:
        require_final_deliverables(data)

    suffix = "" if args.final else "_draft"
    output = REPORT_DIR / "output" / "pdf" / f"cv_hw3_task1_report{suffix}.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=2.1 * cm,
        leftMargin=2.1 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.9 * cm,
        title="CV HW3 Task 1 Report",
        author=f"{data['student_name']} {data['student_id']}",
    )
    styles = build_styles()
    document.build(make_story(data, styles), onFirstPage=footer, onLaterPages=footer)
    print(output)

    if args.publish:
        if not args.final:
            raise RuntimeError("--publish requires --final")
        published = REPORT_DIR / "cv_hw3_task1_report.pdf"
        shutil.copy2(output, published)
        print(published)


if __name__ == "__main__":
    main()
