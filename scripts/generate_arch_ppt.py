from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape
import zipfile


EMU_PER_INCH = 914400
SLIDE_W = 13.333 * EMU_PER_INCH
SLIDE_H = 7.5 * EMU_PER_INCH


def emu(value_in_inches: float) -> int:
    return int(value_in_inches * EMU_PER_INCH)


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float
    text: str
    fill: str = "FFFFFF"
    line: str = "D0D7DE"
    color: str = "111111"
    font_size: int = 2200
    bold: bool = False
    align: str = "ctr"


@dataclass
class LineItem:
    text: str
    level: int = 0


def textbox_xml(shape_id: int, name: str, box: Box) -> str:
    x = emu(box.x)
    y = emu(box.y)
    w = emu(box.w)
    h = emu(box.h)
    lines = box.text.split("\n")
    paras = []
    for idx, line in enumerate(lines):
        line_text = escape(line)
        end_para = '<a:endParaRPr lang="zh-CN" sz="{sz}"/>'.format(sz=box.font_size)
        run_props = 'lang="zh-CN" sz="{sz}" b="{b}"'.format(
            sz=box.font_size,
            b="1" if box.bold else "0",
        )
        body = (
            f'<a:p><a:pPr algn="{box.align}"/>'
            f'<a:r><a:rPr {run_props} dirty="0" smtClean="0">'
            f'<a:solidFill><a:srgbClr val="{box.color}"/></a:solidFill>'
            f'</a:rPr><a:t>{line_text}</a:t></a:r>{end_para}</a:p>'
        )
        if idx == len(lines) - 1 and line == "":
            body = f'<a:p><a:pPr algn="{box.align}"/>{end_para}</a:p>'
        paras.append(body)
    paras_xml = "".join(paras)
    return f"""
    <p:sp>
      <p:nvSpPr>
        <p:cNvPr id="{shape_id}" name="{escape(name)}"/>
        <p:cNvSpPr txBox="1"/>
        <p:nvPr/>
      </p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>
        <a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>
        <a:solidFill><a:srgbClr val="{box.fill}"/></a:solidFill>
        <a:ln w="12700"><a:solidFill><a:srgbClr val="{box.line}"/></a:solidFill></a:ln>
      </p:spPr>
      <p:txBody>
        <a:bodyPr wrap="square" rtlCol="0" anchor="ctr"/>
        <a:lstStyle/>
        {paras_xml}
      </p:txBody>
    </p:sp>
    """.strip()


def title_box(shape_id: int, text: str) -> str:
    return textbox_xml(
        shape_id,
        "Title",
        Box(0.55, 0.35, 12.1, 0.65, text, fill="FFFFFF", line="FFFFFF", color="0F172A", font_size=2800, bold=True, align="l"),
    )


def subtitle_box(shape_id: int, text: str) -> str:
    return textbox_xml(
        shape_id,
        "Subtitle",
        Box(0.6, 1.0, 11.8, 0.42, text, fill="FFFFFF", line="FFFFFF", color="475569", font_size=1400, bold=False, align="l"),
    )


def arrow_textbox(shape_id: int, text: str, x: float, y: float) -> str:
    return textbox_xml(
        shape_id,
        f"Arrow{shape_id}",
        Box(x, y, 0.55, 0.45, text, fill="FFFFFF", line="FFFFFF", color="64748B", font_size=2400, bold=True),
    )


def bullet_box_xml(shape_id: int, x: float, y: float, w: float, h: float, title: str, items: Iterable[LineItem]) -> str:
    paragraphs = []
    paragraphs.append(
        f'<a:p><a:pPr algn="l"/><a:r><a:rPr lang="zh-CN" sz="2200" b="1"><a:solidFill><a:srgbClr val="0F172A"/></a:solidFill></a:rPr><a:t>{escape(title)}</a:t></a:r><a:endParaRPr lang="zh-CN" sz="2200"/></a:p>'
    )
    for item in items:
        level = max(0, item.level)
        bullet_char = "•" if level == 0 else "◦"
        margin = 228600 + (level * 228600)
        indent = -171450
        text = escape(f"{bullet_char} {item.text}")
        paragraphs.append(
            f'<a:p><a:pPr algn="l" marL="{margin}" indent="{indent}"/><a:r><a:rPr lang="zh-CN" sz="1600" b="0"><a:solidFill><a:srgbClr val="334155"/></a:solidFill></a:rPr><a:t>{text}</a:t></a:r><a:endParaRPr lang="zh-CN" sz="1600"/></a:p>'
        )
    paragraphs_xml = "".join(paragraphs)
    return f"""
    <p:sp>
      <p:nvSpPr>
        <p:cNvPr id="{shape_id}" name="BulletBox{shape_id}"/>
        <p:cNvSpPr txBox="1"/>
        <p:nvPr/>
      </p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
        <a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>
        <a:solidFill><a:srgbClr val="F8FAFC"/></a:solidFill>
        <a:ln w="12700"><a:solidFill><a:srgbClr val="E2E8F0"/></a:solidFill></a:ln>
      </p:spPr>
      <p:txBody>
        <a:bodyPr wrap="square" rtlCol="0" lIns="91440" tIns="68580" rIns="91440" bIns="68580"/>
        <a:lstStyle/>
        {paragraphs_xml}
      </p:txBody>
    </p:sp>
    """.strip()


def slide_xml(shapes: list[str]) -> str:
    shapes_xml = "\n".join(shapes)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      {shapes_xml}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>
"""


def make_slide1() -> str:
    shapes = [
        textbox_xml(2, "MainTitle", Box(0.7, 1.3, 11.8, 1.1, "JiuwenSwarm 项目整体架构", fill="E8F0FE", line="E8F0FE", color="0F172A", font_size=3200, bold=True, align="ctr")),
        textbox_xml(3, "SubTitle", Box(2.2, 2.65, 8.9, 0.65, "汇报版架构说明与核心调用链", fill="FFFFFF", line="FFFFFF", color="475569", font_size=1800, align="ctr")),
        bullet_box_xml(4, 1.2, 4.0, 10.9, 1.8, "本页重点", [
            LineItem("双进程架构：Gateway 负责接入治理，AgentServer 负责执行运行时"),
            LineItem("多渠道统一接入：Web、TUI、ACP 与多 IM 平台"),
            LineItem("核心能力可扩展：Skill、Memory、Team、Sandbox"),
        ]),
        textbox_xml(5, "Footer", Box(0.7, 6.85, 12.0, 0.28, "生成时间：2026-06-15    输出文件：JiuwenSwarm_项目整体架构汇报版.pptx", fill="FFFFFF", line="FFFFFF", color="64748B", font_size=1100, align="r")),
    ]
    return slide_xml(shapes)


def make_slide2() -> str:
    shapes = [
        title_box(2, "一页总览"),
        subtitle_box(3, "适合首页展示，突出系统从入口到执行再到基础能力的主链路"),
        textbox_xml(4, "U", Box(0.5, 2.55, 2.1, 1.0, "用户与\n外部入口", fill="E0F2FE", line="BAE6FD", color="0C4A6E", font_size=2200, bold=True)),
        arrow_textbox(5, "→", 2.7, 2.82),
        textbox_xml(6, "C", Box(3.2, 2.55, 2.1, 1.0, "多渠道接入层\nWeb / TUI / ACP / IM", fill="DCFCE7", line="BBF7D0", color="14532D", font_size=1800, bold=True)),
        arrow_textbox(7, "→", 5.4, 2.82),
        textbox_xml(8, "G", Box(5.9, 2.55, 2.1, 1.0, "Gateway\n接入管理 / 路由 / Cron", fill="FEF3C7", line="FDE68A", color="78350F", font_size=1800, bold=True)),
        arrow_textbox(9, "→", 8.1, 2.82),
        textbox_xml(10, "A", Box(8.6, 2.55, 2.15, 1.0, "AgentServer\n会话 / 运行时 / 技能", fill="F3E8FF", line="E9D5FF", color="581C87", font_size=1800, bold=True)),
        arrow_textbox(11, "→", 10.85, 2.82),
        textbox_xml(12, "I", Box(11.45, 2.55, 1.35, 1.0, "基础能力\nLLM 等", fill="FEE2E2", line="FECACA", color="7F1D1D", font_size=1700, bold=True)),
        bullet_box_xml(13, 0.8, 4.35, 12.0, 1.75, "管理层结论", [
            LineItem("入口层统一承接不同终端与第三方平台"),
            LineItem("Gateway 层做协议转换、消息治理与统一转发"),
            LineItem("AgentServer 聚焦执行控制，基础能力层支撑模型与扩展"),
        ]),
    ]
    return slide_xml(shapes)


def make_slide3() -> str:
    shapes = [
        title_box(2, "分层架构"),
        subtitle_box(3, "适合系统设计页，保留关键模块，避免实现细节过多"),
        textbox_xml(4, "L1", Box(0.7, 1.7, 12.0, 0.78, "入口层：Web / TUI / ACP / IM", fill="DBEAFE", line="BFDBFE", color="1E3A8A", font_size=2200, bold=True, align="l")),
        textbox_xml(5, "L2", Box(0.7, 2.65, 12.0, 1.02, "接入与治理层：Gateway / ChannelManager / MessageHandler / Heartbeat / Cron", fill="DCFCE7", line="BBF7D0", color="166534", font_size=2000, bold=True, align="l")),
        textbox_xml(6, "L3", Box(0.7, 3.9, 12.0, 1.08, "执行运行时：AgentServer / AgentManager / JiuWenSwarm Runtime / SessionManager / SkillManager", fill="FEF3C7", line="FDE68A", color="854D0E", font_size=1900, bold=True, align="l")),
        textbox_xml(7, "L4", Box(0.7, 5.2, 12.0, 1.05, "基础设施与外部依赖：LLM / OpenJiuwen / History / Config / Extension / Memory Hook / JiuwenBox Sandbox", fill="F3E8FF", line="E9D5FF", color="6B21A8", font_size=1800, bold=True, align="l")),
        bullet_box_xml(8, 8.35, 1.55, 4.05, 1.35, "设计原则", [
            LineItem("接入层与执行层解耦"),
            LineItem("统一消息模型贯穿全链路"),
            LineItem("能力组件可横向扩展"),
        ]),
    ]
    return slide_xml(shapes)


def make_slide4() -> str:
    shapes = [
        title_box(2, "核心调用链"),
        subtitle_box(3, "以 Web 对话场景为例，展示从请求进入到结果回推的关键环节"),
        textbox_xml(4, "S1", Box(0.55, 2.0, 1.85, 0.88, "1\nBrowser", fill="E0F2FE", line="BAE6FD", color="0C4A6E", font_size=2100, bold=True)),
        arrow_textbox(5, "→", 2.45, 2.22),
        textbox_xml(6, "S2", Box(2.9, 2.0, 1.95, 0.88, "2\nWebChannel", fill="DCFCE7", line="BBF7D0", color="14532D", font_size=2000, bold=True)),
        arrow_textbox(7, "→", 4.92, 2.22),
        textbox_xml(8, "S3", Box(5.35, 2.0, 2.0, 0.88, "3\nMessageHandler", fill="FEF3C7", line="FDE68A", color="78350F", font_size=1900, bold=True)),
        arrow_textbox(9, "→", 7.4, 2.22),
        textbox_xml(10, "S4", Box(7.85, 2.0, 2.0, 0.88, "4\nAgentServer", fill="F3E8FF", line="E9D5FF", color="581C87", font_size=2000, bold=True)),
        arrow_textbox(11, "→", 9.9, 2.22),
        textbox_xml(12, "S5", Box(10.35, 2.0, 2.35, 0.88, "5\nRuntime + Adapter", fill="FEE2E2", line="FECACA", color="7F1D1D", font_size=1900, bold=True)),
        bullet_box_xml(13, 0.75, 3.4, 5.9, 2.35, "主链步骤", [
            LineItem("WebChannel 解析请求并生成内部 Message"),
            LineItem("MessageHandler 处理状态、控制逻辑与转发"),
            LineItem("AgentServer 获取 Agent 实例并调度 Runtime"),
            LineItem("Runtime 写历史、做记忆增强并调用 Adapter"),
            LineItem("结果原路回传到前端，支持流式返回"),
        ]),
        bullet_box_xml(14, 6.9, 3.4, 5.25, 2.35, "评审要点", [
            LineItem("Gateway 不执行 Agent，只做接入治理"),
            LineItem("SessionManager 控制同 session 串行"),
            LineItem("Adapter 屏蔽底层模型与工具差异"),
            LineItem("回传链路与请求链路对称，便于追踪"),
        ]),
    ]
    return slide_xml(shapes)


def make_slide5() -> str:
    shapes = [
        title_box(2, "价值与演进"),
        subtitle_box(3, "适合结论页，强调当前收益与后续扩展方向"),
        bullet_box_xml(4, 0.65, 1.7, 4.0, 3.9, "当前价值", [
            LineItem("双进程解耦，职责清晰"),
            LineItem("多渠道统一接入，前后端链路统一"),
            LineItem("支持会话、技能、记忆、团队与流式响应"),
            LineItem("扩展机制完善，便于接入新能力"),
        ]),
        bullet_box_xml(5, 4.9, 1.7, 4.0, 3.9, "架构亮点", [
            LineItem("统一消息模型"),
            LineItem("Gateway 负责治理"),
            LineItem("AgentServer 聚焦执行"),
            LineItem("Sandbox 支撑安全隔离"),
        ]),
        bullet_box_xml(6, 9.15, 1.7, 3.55, 3.9, "后续演进", [
            LineItem("多实例部署"),
            LineItem("分布式 Team 协作"),
            LineItem("远程执行与沙箱增强"),
            LineItem("技能与检索能力继续增强"),
        ]),
        textbox_xml(7, "Summary", Box(0.85, 6.0, 11.8, 0.72, "一句话总结：JiuwenSwarm 采用“统一接入、网关治理、运行时执行、基础能力解耦”的分层架构，兼顾扩展性、治理能力与演进空间。", fill="EFF6FF", line="DBEAFE", color="1E3A8A", font_size=1700, bold=True, align="l")),
    ]
    return slide_xml(shapes)


def content_types(slide_count: int) -> str:
    slide_overrides = "\n".join(
        f'  <Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
{slide_overrides}
</Types>
"""


ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""


def presentation_xml(slide_count: int) -> str:
    sld_ids = "\n".join(
        f'    <p:sldId id="{255 + i}" r:id="rId{i + 1}"/>'
        for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" saveSubsetFonts="1" autoCompressPictures="0">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId{slide_count + 1}"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
{sld_ids}
  </p:sldIdLst>
  <p:sldSz cx="{int(SLIDE_W)}" cy="{int(SLIDE_H)}" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>
"""


def presentation_rels(slide_count: int) -> str:
    slide_rels = "\n".join(
        f'  <Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{slide_rels}
  <Relationship Id="rId{slide_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
</Relationships>
"""


SLIDE_MASTER = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld name="Simple Slide Master">
    <p:bg>
      <p:bgPr>
        <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
        <a:effectLst/>
      </p:bgPr>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" bg1="lt1" bg2="lt2" folHlink="folHlink" hlink="hlink" tx1="dk1" tx2="dk2"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="1" r:id="rId1"/>
  </p:sldLayoutIdLst>
  <p:txStyles>
    <p:titleStyle/>
    <p:bodyStyle/>
    <p:otherStyle/>
  </p:txStyles>
</p:sldMaster>
"""


SLIDE_MASTER_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>
"""


SLIDE_LAYOUT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank">
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>
"""


THEME = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Simple Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:srgbClr val="000000"/></a:dk1>
      <a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="1F2937"/></a:dk2>
      <a:lt2><a:srgbClr val="F8FAFC"/></a:lt2>
      <a:accent1><a:srgbClr val="2563EB"/></a:accent1>
      <a:accent2><a:srgbClr val="16A34A"/></a:accent2>
      <a:accent3><a:srgbClr val="D97706"/></a:accent3>
      <a:accent4><a:srgbClr val="7C3AED"/></a:accent4>
      <a:accent5><a:srgbClr val="DC2626"/></a:accent5>
      <a:accent6><a:srgbClr val="0891B2"/></a:accent6>
      <a:hlink><a:srgbClr val="2563EB"/></a:hlink>
      <a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Simple">
      <a:majorFont>
        <a:latin typeface="Aptos"/>
        <a:ea typeface="Microsoft YaHei"/>
        <a:cs typeface="Arial"/>
      </a:majorFont>
      <a:minorFont>
        <a:latin typeface="Aptos"/>
        <a:ea typeface="Microsoft YaHei"/>
        <a:cs typeface="Arial"/>
      </a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Simple">
      <a:fillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"/></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"/></a:gs></a:gsLst><a:lin ang="5400000" scaled="0"/></a:gradFill>
        <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"/></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"/></a:gs></a:gsLst><a:lin ang="5400000" scaled="0"/></a:gradFill>
      </a:fillStyleLst>
      <a:lnStyleLst>
        <a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
        <a:ln w="25400"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
        <a:ln w="38100"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
      </a:lnStyleLst>
      <a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
      <a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
  <a:objectDefaults/>
  <a:extraClrSchemeLst/>
</a:theme>
"""


CORE_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>JiuwenSwarm 项目整体架构汇报版</dc:title>
  <dc:subject>项目架构汇报</dc:subject>
  <dc:creator>TRAE Assistant</dc:creator>
  <cp:keywords>JiuwenSwarm, Architecture, PPT</cp:keywords>
  <dc:description>自动生成的项目整体架构汇报版 PowerPoint</dc:description>
  <cp:lastModifiedBy>TRAE Assistant</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">2026-06-15T00:00:00Z</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">2026-06-15T00:00:00Z</dcterms:modified>
</cp:coreProperties>
"""


APP_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Office PowerPoint</Application>
  <PresentationFormat>On-screen Show (16:9)</PresentationFormat>
  <Slides>5</Slides>
  <Notes>0</Notes>
  <HiddenSlides>0</HiddenSlides>
  <MMClips>0</MMClips>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs>
    <vt:vector size="2" baseType="variant">
      <vt:variant><vt:lpstr>主题</vt:lpstr></vt:variant>
      <vt:variant><vt:i4>1</vt:i4></vt:variant>
    </vt:vector>
  </HeadingPairs>
  <TitlesOfParts>
    <vt:vector size="5" baseType="lpstr">
      <vt:lpstr>封面</vt:lpstr>
      <vt:lpstr>一页总览</vt:lpstr>
      <vt:lpstr>分层架构</vt:lpstr>
      <vt:lpstr>核心调用链</vt:lpstr>
      <vt:lpstr>价值与演进</vt:lpstr>
    </vt:vector>
  </TitlesOfParts>
  <Company>TRAE</Company>
  <LinksUpToDate>false</LinksUpToDate>
  <SharedDoc>false</SharedDoc>
  <HyperlinksChanged>false</HyperlinksChanged>
  <AppVersion>16.0000</AppVersion>
</Properties>
"""


SLIDE_LAYOUT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>
"""


SLIDE_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>
"""


def build_pptx(output_path: Path) -> None:
    slides = [
        make_slide1(),
        make_slide2(),
        make_slide3(),
        make_slide4(),
        make_slide5(),
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types(len(slides)))
        zf.writestr("_rels/.rels", ROOT_RELS)
        zf.writestr("docProps/core.xml", CORE_XML)
        zf.writestr("docProps/app.xml", APP_XML)
        zf.writestr("ppt/presentation.xml", presentation_xml(len(slides)))
        zf.writestr("ppt/_rels/presentation.xml.rels", presentation_rels(len(slides)))
        zf.writestr("ppt/slideMasters/slideMaster1.xml", SLIDE_MASTER)
        zf.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", SLIDE_MASTER_RELS)
        zf.writestr("ppt/slideLayouts/slideLayout1.xml", SLIDE_LAYOUT)
        zf.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", SLIDE_LAYOUT_RELS)
        zf.writestr("ppt/theme/theme1.xml", THEME)
        for idx, slide in enumerate(slides, start=1):
            zf.writestr(f"ppt/slides/slide{idx}.xml", slide)
            zf.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", SLIDE_RELS)


if __name__ == "__main__":
    out = Path("/workspace/docs/zh/JiuwenSwarm_项目整体架构汇报版.pptx")
    build_pptx(out)
    print(out)
