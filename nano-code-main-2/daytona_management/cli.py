import sys
from .proxy import NanoCodeProxy


def show_help():
    """显示使用帮助"""
    print("=" * 60)
    print("🚀 nano-code 智能任务执行")
    print("")
    print("💡 使用方法:")
    print("   python3 daytona_proxy.py \"任务描述\"")
    print("")
    print("📖 示例 (智能模式 - Agent自动选择工具):")
    print("   python3 daytona_proxy.py \"分析CSV数据\"")
    print("   python3 daytona_proxy.py \"分析这个数据文件 data.csv\"")
    print("   python3 daytona_proxy.py \"分析并可视化这两个数据 /path/file1.csv /path/file2.csv\"")
    print("   python3 daytona_proxy.py \"检查main.py和config.py的代码质量\"")
    print("   python3 daytona_proxy.py \"分析https://github.com/user/project的代码架构\"")
    print("   python3 daytona_proxy.py \"比较本地文件main.py和仓库https://github.com/user/repo\"")
    print("")
    print("🧠 Agent会自动:")
    print("   - 识别Git仓库URL并克隆分析")
    print("   - 检测文件名并读取内容")  
    print("   - 根据任务描述选择合适的工具")
    print("   - 智能决定执行策略")


def parse_arguments() -> dict:
    # 检查基本参数
    if len(sys.argv) < 2:
        return {"show_help": True}
    
    # 所有参数合并为原始用户输入
    user_input = " ".join(sys.argv[1:])
    
    return {
        "user_input": user_input,
        "show_help": False
    }


def main():
    """主入口函数"""
    try:
        # 解析参数
        args = parse_arguments()
        
        if args.get("show_help"):
            show_help()
            sys.exit(0)
        
        # 创建代理实例
        proxy = NanoCodeProxy()
        proxy.setup_daytona()
        
        print("=" * 60)
        print("🎯 nano-code 智能执行")
        print(f"📋 用户输入: {args['user_input']}")
        print("=" * 60)
        
        proxy.start_nano_code_unified(args["user_input"])
        
    except KeyboardInterrupt:
        print("\n👋 程序被中断")
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()