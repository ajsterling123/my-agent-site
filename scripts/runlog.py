#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""runlog.py —— 构建与抓取脚本统一走它写运行日志（Step 10）。

每条事件是一行 JSON（JSONL），追加写进 logs/build.log 并同步输出到 stdout——
CI 的 stdout 因此天然就是一份完整日志。字段即课程要求的七要素：

  time    ISO 8601 带 +08:00 时区；
  run_id  本次运行的唯一标识（UTC 时间戳 + 4 位随机十六进制），一次运行一个；
  task    脚本名（如 build_wiki）；
  input   输入摘要（查询词、源数、条数这类；不含文章/论文正文内容）；
  action  做了什么（ASCII 短语，如 read_input / render_pages / write_outputs）；
  result  "ok" / "fail"；
  error   失败原因（没有失败则省略这个键）。

run_id 在运行结束时打印到 stdout 最后一行（RunLog.finish()，放在 finally 里调），
便于把本地 logs/build.log 里的段落与 Actions 日志按 run_id 关联。

脱敏是硬规则（课程原文要求）：任何键名匹配 /secret|token|key|password/i 的值
一律遮蔽为 "***"；字符串值里出现的邮箱地址同样遮蔽——邮箱正文、Webhook 地址
这类值不写进日志。input 里只放计数与查询词，不放抓取到的正文。

logs/ 不进仓库（.gitignore 已排除）：日志是追加性的，每次构建都会变，提交进
仓库会弄脏工作树、破坏「重复构建 git status 干净」这条验收。
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "logs" / "build.log"

# 站点在中国，日志时间统一 +08:00（与 feed 的 FEED_TZ 同一口径，不依赖构建机时区）。
TZ = timezone(timedelta(hours=8))

SENSITIVE_KEY_RE = re.compile(r"secret|token|key|password", re.I)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")
# Webhook 地址（hooks.example.com、…/webhook/send 之类）的值不写进日志：URL 里带
# hook 字样的整段遮蔽（课程原文要求；顺带罩住 ?key=… 形式的回调地址）。
WEBHOOK_RE = re.compile(r"https?://[^\s\"'<>]*hook[^\s\"'<>]*", re.I)
MASK = "***"


def scrub(value):
    """递归脱敏：敏感键名的值遮蔽为 ***；字符串值里的 Webhook 地址与邮箱地址同样遮蔽。"""
    if isinstance(value, dict):
        return {k: (MASK if SENSITIVE_KEY_RE.search(str(k)) else scrub(v))
                for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [scrub(v) for v in value]
    if isinstance(value, str):
        return EMAIL_RE.sub(MASK, WEBHOOK_RE.sub(MASK, value))
    return value


def new_run_id():
    """UTC 时间戳 + 4 位随机十六进制，例如 20261009T051230Z-3fa1。"""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return "%s-%s" % (stamp, os.urandom(2).hex())


class RunLog:
    """一次运行一个实例；event() 记事件，finish() 打印 run_id 收尾。"""

    def __init__(self, task, path=LOG_PATH):
        self.task = task
        self.run_id = new_run_id()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def event(self, action, result="ok", error=None, input=None):
        """记一条事件：追加进 logs/build.log 并打印到 stdout。"""
        record = {
            "time": datetime.now(TZ).isoformat(timespec="seconds"),
            "run_id": self.run_id,
            "task": self.task,
            "input": scrub(input if input is not None else {}),
            "action": action,
            "result": result,
        }
        if error is not None:
            record["error"] = scrub("%s" % error)
        line = json.dumps(record, ensure_ascii=False)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        print(line)

    def finish(self):
        """运行结束的收尾：run_id 打到 stdout 最后一行，供与 Actions 日志关联。"""
        try:
            where = self.path.relative_to(ROOT).as_posix()
        except ValueError:
            where = str(self.path)
        print("run_id %s（本次日志已追加进 %s）" % (self.run_id, where))


def wrap_main(task, main, argv=None):
    """脚本入口的统一包装：失败也留下 fail 事件，且 run_id 永远是 stdout 最后一行。

    main() 返回退出码；BuildError 等预期失败记一条 fail 事件后按失败退出；
    意外异常同样先记 fail 事件再原样抛出（保留 traceback）。
    """
    log = RunLog(task)
    try:
        return main(log, argv)
    except Exception as exc:
        error = str(exc) if isinstance(exc, Exception) and str(exc) else type(exc).__name__
        log.event("run", "fail", error=error, input={})
        raise
    finally:
        log.finish()
