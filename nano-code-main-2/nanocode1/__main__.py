import os
import sys
import asyncio
import argparse
from .agent.non_interactive_agent import run_non_interactive_task




def parse_args():
    parser = argparse.ArgumentParser(
        description="nano-code - 智能AI编程助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # 智能模式 - Agent自动分析用户输入
    parser.add_argument(
        "--user-input", "-u",
        required=True,
        help="用户输入 - Agent自动分析并选择工具"
    )
    
    parser.add_argument(
        "--working-dir",
        default=os.getcwd(),
        help="工作目录（默认：当前目录）"
    )
    
    return parser.parse_args()

async def run_batch_mode(args):
    try:
        print("🧠 智能模式：Agent将自动分析用户输入")
        result = await run_non_interactive_task(
            user_input=args.user_input,
            working_dir=args.working_dir
        )
        
        if result['status'] == 'completed':
            print("✅ 任务完成")
        else:
            print("⚠️ 任务未完全完成")
            
        return result
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)


def main():

    args = parse_args()
    asyncio.run(run_batch_mode(args))


if __name__ == "__main__":
    main()