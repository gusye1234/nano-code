import os
import sys
import asyncio
import argparse
from rich.console import Console
from .agent.non_interactive_agent import run_non_interactive_task




def parse_args():

    parser = argparse.ArgumentParser(
        description="nano-code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        
    )
    
    parser.add_argument(
        "--task", "-t",
        required=True,
        help="任务描述（必需）"
    )
    
    parser.add_argument(
        "--files", "-f",
        nargs="*",
        help="输入文件列表"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=20,
        help="最大执行轮次（默认：20）"
    )
    
    parser.add_argument(
        "--working-dir",
        default=os.getcwd(),
        help="工作目录（默认：当前目录）"
    )
    
    return parser.parse_args()

async def run_batch_mode(args):
    """运行批处理模式"""
    print(f"🚀 nano-code ")
    print(f"📋 任务: {args.task}")
    if args.files:
        print(f"📁 输入文件: {len(args.files)} 个")
    
    try:
        result = await run_non_interactive_task(
            task_description=args.task,
            input_files=args.files,
            working_dir=args.working_dir,
            max_iterations=args.max_iterations
        )
        
        if result['status'] == 'completed':
            print("✅ 批处理任务完成")
        else:
            print("⚠️ 批处理任务未完全完成")
            
        return result
        
    except Exception as e:
        print(f"❌ 批处理执行失败: {e}")
        sys.exit(1)


def main():

    args = parse_args()
    asyncio.run(run_batch_mode(args))


if __name__ == "__main__":
    main()