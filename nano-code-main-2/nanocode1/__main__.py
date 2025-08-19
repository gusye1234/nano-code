import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from .agent.non_interactive_agent import run_intelligent_task
from .models.dissertation_plan import DissertationPlan


def parse_args():
    parser = argparse.ArgumentParser(
        description="nanocode1 - AI编程助手 (支持URL分析和JSON任务执行)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "input",
        help="输入内容：URL地址(阶段1)或JSON任务文件路径(阶段2)"
    )
    
    parser.add_argument(
        "--working-dir",
        default=os.getcwd(),
        help="工作目录（默认：当前目录）"
    )
    
    return parser.parse_args()


def detect_input_type(input_str: str) -> dict:
    """智能检测输入类型并构建任务上下文."""
    if input_str.startswith(('http://', 'https://')):
        return {
            "type": "url_analysis",
            "url": input_str
        }
    
    input_path = Path(input_str)
    if input_path.exists() and input_path.suffix == '.json':
        try:
            dissertation_plan = DissertationPlan.from_file(input_str)
            return {
                "type": "json_task_execution", 
                "dissertation_plan": dissertation_plan
            }
        except Exception as e:
            print(f"❌ JSON文件格式错误: {e}")
            sys.exit(1)
    
    print(f"❌ 无效输入: {input_str}")
    print("输入必须是URL(https://...)或JSON文件路径(.json)")
    sys.exit(1)


async def run_agent(args):
    try:
        task_context = detect_input_type(args.input)
        
        result = await run_intelligent_task(
            task_context=task_context,
            working_dir=args.working_dir
        )
        
        if result['status'] == 'completed':
            print("✅ 任务完成")
            if result.get('phase') == 'url_analysis':
                print("📄 代码分析文档已生成")
            elif result.get('phase') == 'json_task_execution':
                print("🎯 JSON任务执行完成")
        else:
            print("⚠️ 任务未完全完成")
            
        return result
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)


def main():
    args = parse_args()
    asyncio.run(run_agent(args))


if __name__ == "__main__":
    main()