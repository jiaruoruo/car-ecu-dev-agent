#!/usr/bin/env python3
"""
upgrade_skills_format.py
根据 create-automotive-skill/SKILL.md 模板格式，批量升级 skills 目录下各 SKILL.md：
  1. knowledge_areas: area: → primary-area: / secondary-area:
  2. instructions: ### A/B/C/D/E 格式 → yaml 代码块 段落 A/B/C/D 格式
  3. 在 validation 后插入 human_checks 段落
跳过: create-automotive-agent, create-automotive-skill, tlf35584, test999
"""

import re
from pathlib import Path

BASE = Path("d:/AI/myproject/driver-hal-develop/skills")
SKIP = {"create-automotive-agent", "create-automotive-skill", "tlf35584", "test999"}

# ── human_checks 内容（按 skill 定制）────────────────────────────────────────
HUMAN_CHECKS = {
    "bridge-driver": """\
```yaml
human_checks:
  - condition: "桥式驱动用于 ASIL-C/D 安全关键执行器（如电动助力转向/制动执行器）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查故障检测逻辑与保护响应时间"

  - condition: "PWM 死区时间或交叉导通防护参数变更"
    action: "必须触发 HUMAN CHECK，确认新参数满足驱动芯片交叉导通防护要求"

  - condition: "故障检测状态机逻辑变更（过流/过温/欠压保护路径修改）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认保护动作的及时性和完整性"

  - condition: "SPI 通信失败时安全状态（关闭 PWM 输出）处理策略变更"
    action: "必须触发 HUMAN CHECK，防止修改导致执行器失控"

  - condition: "tools_required 包含直接写入生产 ECU 驱动芯片控制寄存器的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的驱动配置进入生产环境"
```""",

    "can": """\
```yaml
human_checks:
  - condition: "CAN/CANFD 总线承载 ASIL-C/D 安全关键信号"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查 E2E 保护配置与 Bus-Off 恢复策略"

  - condition: "波特率或采样点配置变更（影响 ISO 11898 合规性）"
    action: "必须触发 HUMAN CHECK，确认新波特率误差 ≤ ±1.5% 并通知相关网络节点评估影响"

  - condition: "Bus-Off 自动恢复策略变更（恢复间隔/最大尝试次数）"
    action: "必须触发 HUMAN CHECK，确认新策略不会导致安全关键报文在 Bus-Off 期间丢失"

  - condition: "CAN 硬件报文过滤器配置变更（可能导致安全关键帧被过滤丢弃）"
    action: "必须触发 HUMAN CHECK，验证安全关键 CAN ID 不在新过滤规则的屏蔽范围内"

  - condition: "tools_required 包含直接修改生产 ECU CAN 网络配置的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的网络配置影响整车通信"
```""",

    "eth": """\
```yaml
human_checks:
  - condition: "以太网用于 ASIL-B 及以上安全通信链路（SOME-IP 安全服务/AVTP）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查 E2E 保护与 VLAN 安全配置"

  - condition: "MAC 地址或 VLAN 优先级配置变更（影响安全帧路由）"
    action: "必须触发 HUMAN CHECK，确认新配置不会导致安全关键以太网帧被丢弃或误路由"

  - condition: "DMA 描述符数量或缓冲区大小变更（可能导致帧丢弃）"
    action: "必须触发 HUMAN CHECK，确认新缓冲区配置能处理最大报文突发而不丢帧"

  - condition: "PHY Link Down 事件的安全响应策略变更"
    action: "必须触发 HUMAN CHECK，确认新策略满足应用层对链路断开的安全降级要求"

  - condition: "tools_required 包含直接操作生产 ECU 以太网网络配置的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的网络配置影响车载以太网安全"
```""",

    "ex-flash": """\
```yaml
human_checks:
  - condition: "Flash 存储 ASIL-B 及以上安全关键参数（标定/配置/安全参数）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查数据完整性机制（CRC/ECC/冗余写入）"

  - condition: "Flash 写保护区域配置变更（BP0-BP3/CMP 位）"
    action: "必须触发 HUMAN CHECK，确认新保护配置不会意外暴露安全关键存储区域"

  - condition: "掉电恢复机制逻辑变更（写中断后的数据恢复流程修改）"
    action: "必须触发 HUMAN CHECK，确认新恢复逻辑能正确处理所有写中断场景"

  - condition: "Flash 操作超时阈值变更（WIP 轮询最大等待时间）"
    action: "必须触发 HUMAN CHECK，确认新超时阈值在最坏温度条件下仍能正确等待操作完成"

  - condition: "tools_required 包含直接修改生产 ECU Flash 内容的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的 Flash 写入操作影响 ECU 正常工作"
```""",

    "fsi": """\
```yaml
human_checks:
  - condition: "FSI 帧周期或超时阈值配置变更（直接影响 ASIL-D 安全响应时间）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认新配置满足系统 ASIL-D 安全响应时间要求"

  - condition: "FSI CRC-8 算法或初值配置变更"
    action: "必须触发 HUMAN CHECK，确认新算法仍能覆盖全部数据完整性保护要求"

  - condition: "FSI 安全状态机（SafeState 进入/退出条件）逻辑修改"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认 SafeState 触发条件和系统安全响应正确"

  - condition: "FSI 通信故障容忍次数或分级处理策略变更"
    action: "必须触发 HUMAN CHECK，确认新策略不会延迟 ASIL-D 安全关键故障的响应"

  - condition: "FSI 驱动被定义为 ASIL-D 安全通信路径的唯一实现，无独立评审"
    action: "拒绝执行，必须触发 HUMAN CHECK，要求增加独立功能安全评审流程"

  - condition: "tools_required 包含直接写入 FSI 安全关键配置寄存器的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的 FSI 配置引入 ASIL-D 安全违规"
```""",

    "hsd-lsd-driver": """\
```yaml
human_checks:
  - condition: "HSD/LSD 控制 ASIL-C/D 安全关键执行器（制动灯/转向信号/安全阀门）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查保护逻辑与故障检测响应时间"

  - condition: "过流/短路/开路故障检测阈值变更"
    action: "必须触发 HUMAN CHECK，确认新阈值在最坏工况下仍能正确检测故障而不误报"

  - condition: "故障检测到保护动作（关闭负载输出）的响应时序变更"
    action: "必须触发 HUMAN CHECK，确认新响应时序满足安全目标规定的最大容错时间"

  - condition: "IS 电流反馈采样逻辑变更（限流保护参数修改）"
    action: "必须触发 HUMAN CHECK，确认新限流阈值与负载规格和 ASIL 安全要求一致"

  - condition: "tools_required 包含直接控制生产 ECU HSD/LSD 输出引脚的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的负载控制操作损坏执行器或引发安全事件"
```""",

    "i2c": """\
```yaml
human_checks:
  - condition: "I2C 用于 ASIL-B 及以上安全关键传感器通信"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查超时配置与通信错误恢复机制"

  - condition: "I2C 总线超时阈值变更（影响总线死锁恢复时间）"
    action: "必须触发 HUMAN CHECK，确认新超时值在最坏工况下能正确检测总线故障"

  - condition: "I2C 从设备地址配置变更（影响设备识别与数据路由）"
    action: "必须触发 HUMAN CHECK，确认新地址配置与硬件电路一致，无地址冲突"

  - condition: "总线死锁恢复策略变更（SCL 脉冲复位逻辑修改）"
    action: "必须触发 HUMAN CHECK，确认新恢复策略在所有死锁场景下均能正确恢复总线"

  - condition: "tools_required 包含直接操作生产 ECU I2C 传感器配置的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的 I2C 配置影响传感器采集精度"
```""",

    "mcu": """\
```yaml
human_checks:
  - condition: "系统时钟配置变更（PLL 参数/分频系数）影响 ASIL-D 安全功能实时性"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认新时钟配置满足所有安全任务的时序要求"

  - condition: "时钟监控（CMU）配置变更（监控范围/报警阈值/报警响应）"
    action: "必须触发 HUMAN CHECK，确认新配置能在规定时间内检测到时钟失效并触发安全响应"

  - condition: "低功耗模式配置变更（SLEEP/STANDBY 进入/唤醒条件）"
    action: "必须触发 HUMAN CHECK，确认低功耗模式下 ASIL-D 安全功能（WDG/FSI）不被中断"

  - condition: "复位后初始化序列变更（影响系统安全上电时序）"
    action: "必须触发 HUMAN CHECK，确认新上电序列满足 PMIC 与 MCU 安全联动时序要求"

  - condition: "MCU 被定义为 ASIL-D 系统的主控制单元，时钟配置无独立评审"
    action: "拒绝执行，必须触发 HUMAN CHECK，要求功能安全工程师书面确认时钟配置"
```""",

    "port": """\
```yaml
human_checks:
  - condition: "ASIL-B 及以上安全关键执行器控制引脚的初始电平配置变更"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认新初始电平不会在 ECU 上电期间触发意外执行器动作"

  - condition: "安全关键引脚（nFAULT/nSLEEP/EN/SAFE）方向或复用功能变更"
    action: "必须触发 HUMAN CHECK，确认变更不会影响安全监控信号的传输路径"

  - condition: "SPI/CAN/ETH 通信引脚复用功能变更（可能导致通信静默）"
    action: "必须触发 HUMAN CHECK，确认新复用功能配置与硬件电路一致，通信功能正常"

  - condition: "引脚驱动强度变更（影响信号完整性和 EMC 性能）"
    action: "必须触发 HUMAN CHECK，确认新驱动强度满足 EMC 规范，不引入干扰"

  - condition: "tools_required 包含直接修改生产 ECU 引脚配置的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的引脚变更导致硬件损坏或功能失效"
```""",

    "safetypack": """\
```yaml
human_checks:
  - condition: "Safety Pack 监控窗口时间参数变更（周期/容差/故障阈值）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认新参数满足系统 ASIL-D 安全响应时间要求"

  - condition: "故障反应函数逻辑变更（安全状态转换条件或响应动作修改）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认新故障反应满足安全目标要求"

  - condition: "Safety Pack 与 FSI/WDG/PMIC 联动逻辑变更"
    action: "必须触发 HUMAN CHECK，确认联动变更不会导致安全机制失效或误触发"

  - condition: "安全状态不可逆性约束变更（允许从安全状态自动恢复的条件修改）"
    action: "必须触发 HUMAN CHECK，确认新策略不会绕过安全状态恢复到正常运行模式"

  - condition: "Safety Pack 驱动被定义为 ASIL-D 安全机制的唯一实现路径，无独立评审"
    action: "拒绝执行，必须触发 HUMAN CHECK，要求增加独立功能安全评审流程"

  - condition: "tools_required 包含直接写入生产 ECU Safety Pack 配置寄存器的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的 Safety Pack 配置进入生产环境"
```""",

    "sensor1-driver": """\
```yaml
human_checks:
  - condition: "安全关键传感器（制动/转向/ASIL-B 及以上）故障检测逻辑变更"
    action: "必须触发 HUMAN CHECK，由功能安全工程师确认新检测逻辑满足 ASIL 故障检测时间要求"

  - condition: "传感器断线/短路检测阈值变更（可能导致漏检或误报）"
    action: "必须触发 HUMAN CHECK，确认新阈值在最坏工况（温度/电压波动）下仍能正确检测故障"

  - condition: "标定参数存储格式或 CRC 校验策略变更"
    action: "必须触发 HUMAN CHECK，确认变更后旧标定数据能被正确迁移，不引入测量偏差"

  - condition: "传感器信号滤波参数变更（影响响应时间和噪声抑制）"
    action: "必须触发 HUMAN CHECK，确认新滤波参数满足应用层对传感器响应时间的要求"

  - condition: "tools_required 包含直接修改生产 ECU 传感器标定参数的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的标定数据写入导致测量错误"
```""",

    "spi": """\
```yaml
human_checks:
  - condition: "SPI 用于 ASIL-B 及以上安全关键设备通信（PMIC/HSD/FSI）"
    action: "必须触发 HUMAN CHECK，由功能安全工程师审查 SPI 错误处理完整性与超时配置"

  - condition: "SPI 时序参数变更（CS 建立/保持时间/时钟模式/速率）"
    action: "必须触发 HUMAN CHECK，确认新时序满足最严苛从设备要求，需示波器验证"

  - condition: "多从设备 CS 片选互斥保护机制变更"
    action: "必须触发 HUMAN CHECK，确认新保护机制不会导致 CS 重叠引起总线冲突"

  - condition: "SPI 传输超时处理策略变更（超时后总线恢复逻辑修改）"
    action: "必须触发 HUMAN CHECK，确认新策略能在所有异常场景下正确恢复总线到空闲状态"

  - condition: "tools_required 包含直接操作生产 ECU SPI 设备寄存器的工具权限"
    action: "必须触发 HUMAN CHECK，防止未经评审的 SPI 写操作损坏安全关键设备配置"
```""",
}

# ── 转换 instructions 段落 ────────────────────────────────────────────────────
def _strip_list_prefix(line: str) -> str:
    """移除 Markdown 列表符号前缀 (- / 1. / - **bold**:)"""
    line = re.sub(r'^- \*\*(.*?)\*\*[：:]\s*', r'\1：', line)  # - **xxx**：yyy
    line = re.sub(r'^- \*\*(.*?)\*\*\s*', r'\1 ', line)        # - **xxx** yyy
    line = re.sub(r'^- ', '', line)                              # - item
    line = re.sub(r'^\d+\. ', r'\g<0>', line)                   # 保留序号
    return line


def convert_instructions(old_text: str) -> str:
    """把旧的 ### A/B/C/D/E Markdown 格式转换成 yaml 代码块 + 段落 A/B/C/D 格式"""

    def extract(header_re: str) -> str:
        m = re.search(header_re + r'\n\n(.*?)(?=\n### |\Z)', old_text, re.DOTALL)
        return m.group(1).strip() if m else ""

    approach    = extract(r'### B\. Approach（执行步骤）')
    standards   = extract(r'### C\. Standards & Best Practices（规范遵循）')
    deliverables= extract(r'### D\. Deliverables（交付物定义）')
    safety      = extract(r'### E\. Safety & Security Considerations（安全合规检查）')

    def indent_block(text: str) -> str:
        lines = text.split('\n')
        out = []
        for ln in lines:
            stripped = _strip_list_prefix(ln)
            # 带序号的行保留原样（以数字开头）
            if re.match(r'^\d+\.', stripped):
                out.append('  ' + stripped)
            elif stripped.strip():
                out.append('  ' + stripped)
            else:
                out.append('')
        return '\n'.join(out)

    a = indent_block(approach)
    b = indent_block(standards)
    c = indent_block(deliverables)
    d = indent_block(safety)

    return (
        "```yaml\n"
        "\n"
        "段落 A：Approach（执行步骤）\n"
        "\n"
        f"{a}\n"
        "\n"
        "段落 B：Standards & Best Practices（规范遵循）\n"
        "\n"
        f"{b}\n"
        "\n"
        "段落 C：Deliverables（交付物定义）\n"
        "\n"
        f"{c}\n"
        "\n"
        "段落 D：Safety & Security Considerations（安全合规检查）\n"
        "\n"
        f"{d}\n"
        "\n"
        "```"
    )


# ── 主转换逻辑 ────────────────────────────────────────────────────────────────
def transform_skill(skill_dir: Path):
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        print(f"  SKIP (no SKILL.md): {skill_dir.name}")
        return

    content = skill_file.read_text(encoding="utf-8")

    # 已是新格式则跳过
    if "段落 A：" in content and "human_checks" in content:
        print(f"  SKIP (already new format): {skill_dir.name}")
        return

    # ── 变换 1：knowledge_areas area: → primary-area: / secondary-area: ──
    occ = [0]
    def replace_area(m):
        occ[0] += 1
        return "  - primary-area:" if occ[0] == 1 else "  - secondary-area:"
    content = re.sub(r'  - area:', replace_area, content)

    # ── 变换 2：instructions 段落格式转换 ──────────────────────────────────
    instr_match = re.search(
        r'(\n## instructions\n\n)(.*?)(\n---\n\n## examples)',
        content, re.DOTALL
    )
    if instr_match:
        new_instr_body = convert_instructions(instr_match.group(2))
        content = (
            content[:instr_match.start()]
            + instr_match.group(1)
            + new_instr_body
            + instr_match.group(3)
            + content[instr_match.end():]
        )

    # ── 变换 3：在 ## validation ... --- 后面插入 human_checks ──────────────
    hc_text = HUMAN_CHECKS.get(skill_dir.name, "")
    if hc_text and "human_checks" not in content:
        content = re.sub(
            r'(\n---\n\n## metadata\n)',
            f"\n---\n\n## human_checks\n\n{hc_text}\n\n---\n\n## metadata\n",
            content
        )

    skill_file.write_text(content, encoding="utf-8")
    print(f"  UPDATED: {skill_dir.name}")


# ── 入口 ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    updated = 0
    for d in sorted(BASE.iterdir()):
        if d.is_dir() and d.name not in SKIP:
            transform_skill(d)
            updated += 1
    print(f"\nDone. Processed {updated} skills (skipped: {SKIP})")
