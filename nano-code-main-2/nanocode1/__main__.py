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
        description="nanocode1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "input",
        nargs='?',
        help="JSON文件路径或用户输入"
    )
    
    parser.add_argument(
        "--working-dir",
        default=os.getcwd(),    
        help="工作目录路径"
    )
    
    
    return parser.parse_args()


def load_task_plan(json_file: str) -> DissertationPlan:
    """
    从JSON文件加载任务计划
    Args:
        json_file (str): JSON文件路径
    Returns:
        DissertationPlan: 任务计划对象
    """
    input_path = Path(json_file)
    if not input_path.exists() or input_path.suffix != '.json':
        print(f"❌ 无效输入: {json_file}")
        sys.exit(1)
    
    try:
        return DissertationPlan.from_file(json_file)
    except Exception as e:
        print(f"❌ JSON文件格式错误: {e}")
        sys.exit(1)




async def run_agent(args):
    try:
        if not args.input:
            print("❌ 请提供JSON文件路径")
            sys.exit(1)
            
        dissertation_plan = load_task_plan(args.input)
        
        result = await run_intelligent_task(
            dissertation_plan=dissertation_plan,
            working_dir=args.working_dir
        )
        
        if result['status'] == 'completed':
            print("✅ 任务完成")
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