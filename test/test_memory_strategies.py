import sys
import os
import asyncio
from typing import List, Dict, Any
from datetime import datetime

# 将 agent 目录添加到 Python 路径中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.memory_strategy import create_memory_strategy, BaseMemoryStrategy
from agent.llm_provider import init_llm
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# --- 真实对话场景数据 ---

# 场景1：技术支持对话
TECH_SUPPORT_CONVERSATION = [
    ("我的电脑最近运行很慢，经常卡顿", "我理解您的困扰。让我帮您诊断一下。请问您的电脑是什么操作系统？大概使用了多久？"),
    ("是Windows 11，买了大概2年了", "Windows 11系统2年的使用时间还算比较新。请问您最近有安装什么新软件吗？或者注意到是在运行特定程序时特别卡顿？"),
    ("主要是打开Chrome浏览器的时候，开很多标签页就卡", "Chrome确实比较占用内存。您电脑的内存是多少？可以按Win+Pause查看系统信息。"),
    ("我看了下是8GB内存，现在内存使用率显示85%", "8GB内存对于现代浏览器多标签使用确实有些吃紧。我建议：1) 使用Chrome的标签页分组功能 2) 安装The Great Suspender扩展自动挂起不活跃标签 3) 定期清理浏览器缓存"),
    ("好的，那我的开机也很慢怎么办？要5分钟才能进桌面", "开机5分钟确实太慢了。这通常是启动项过多或者硬盘问题。您的系统盘是固态硬盘还是机械硬盘？"),
    ("应该是机械硬盘，我没有换过", "找到问题了！机械硬盘是主要瓶颈。升级到固态硬盘可以极大提升开机速度和整体响应。一个256GB的固态硬盘作为系统盘，成本不高但效果显著。"),
    ("换固态硬盘会不会很麻烦？我的数据会丢失吗？", "不用担心，可以：1) 使用硬盘克隆工具直接复制系统 2) 或者保留原硬盘作为数据盘，只在新固态上装系统。建议找专业人员帮助，确保数据安全。"),
    ("除了换硬件，还有其他优化方法吗？", "当然有！软件层面可以：1) 禁用不必要的启动项(msconfig) 2) 关闭Windows搜索索引 3) 定期磁盘清理和碎片整理 4) 关闭不需要的视觉效果。这些能改善20-30%的性能。"),
    ("我刚才看了启动项，有20多个程序", "20多个启动项太多了！建议只保留杀毒软件和必要的驱动程序。其他像音乐播放器、下载工具、办公软件等都可以禁用自启动，需要时手动打开即可。"),
    ("好的，我试试看。对了，我的C盘只剩2GB空间了，有影响吗？", "影响很大！Windows需要至少15%的剩余空间才能正常运行。空间不足会导致：1) 无法创建虚拟内存 2) 系统更新失败 3) 临时文件无法生成。请立即清理！"),
]

# 场景2：产品咨询对话（包含上下文依赖）
PRODUCT_CONSULTATION = [
    ("你好，我想了解一下你们的云服务器产品", "您好！我们提供多种云服务器配置。请问您主要用于什么用途？比如网站托管、应用开发、还是数据分析？"),
    ("主要是想搭建一个电商网站，预计日访问量在5万左右", "日访问5万的电商网站，建议选择我们的标准型S3配置：4核8G内存，100G SSD存储，5M带宽。这个配置可以稳定支撑您的业务需求。"),
    ("这个配置的价格是多少？", "标准型S3的价格是：包年2880元（月均240元），包月的话是300元/月。现在有优惠活动，新用户首年可享受7折，只需2016元。"),
    ("听起来不错。数据安全方面有什么保障吗？", "数据安全是我们的重点：1) 三副本存储，任何硬件故障不会丢失数据 2) 每日自动备份，保留7天 3) DDoS防护和Web应用防火墙 4) SSL证书免费提供。"),
    ("如果以后业务增长，需要升级配置麻烦吗？", "升级非常方便！支持在线无缝升级，只需要在控制台操作，5分钟内完成，期间服务不会中断。而且只需要补差价即可，非常灵活。"),
    ("那技术支持怎么样？我不太懂技术", "别担心！我们提供：1) 7×24小时在线客服 2) 详细的视频教程和文档 3) 一键部署常用环境（如WordPress、商城系统）4) 前3个月免费代维护服务。"),
    ("听起来挺全面的。如果我现在购买，多久能用上？", "非常快！下单后5分钟内服务器就会自动开通，您会收到登录信息。如果需要，我们的技术人员可以免费帮您完成初始环境配置，1小时内就能开始使用。"),
    ("我还想问下，这个配置能支持多少个并发用户？", "标准型S3配置在优化良好的情况下，可以支持500-800个并发用户。对于日访问5万的网站来说绰绰有余。而且我们提供CDN加速服务，可以进一步提升用户体验。"),
    ("CDN是额外收费的吗？", "基础CDN服务是包含的，每月有100GB免费流量。超出部分按0.2元/GB计费。一般电商网站配合图片优化，100GB可以支撑15-20万PV，完全够用。"),
    ("明白了。你们支持什么付款方式？可以开发票吗？", "支持支付宝、微信、银行转账等多种方式。可以开具增值税普通发票或专用发票，电子发票实时开具，纸质发票2-3个工作日寄出。"),
    ("我回头和合伙人商量一下。对了，刚才说的S3配置具体是什么参数？", "S3配置的详细参数是：CPU 4核（Intel Xeon Gold），内存8GB DDR4，系统盘100GB SSD，带宽5Mbps（BGP多线），免费提供1个独立IP。这是我们最受欢迎的配置。"),
    ("如果我想先试用一下可以吗？", "当然可以！我们提供7天免费试用，功能与正式版完全相同。试用期间的数据可以无缝转入正式服务。需要我现在帮您开通试用吗？"),
]

# 场景3：学习辅导对话（需要记住学生特点）
TUTORING_CONVERSATION = [
    ("老师，我是小明，高二学生，数学总是学不好", "你好小明！高二数学确实有一定难度。能告诉我具体是哪个部分比较困难吗？是函数、数列、还是立体几何？"),
    ("主要是函数部分，特别是三角函数，完全搞不懂", "三角函数确实是高二的难点。我们从基础开始，你知道正弦、余弦、正切的定义吗？比如在直角三角形中它们分别代表什么？"),
    ("知道定义，就是sin=对边/斜边这些，但是一到做题就蒙了", "理解定义是好的开始！问题可能在于缺乏形象理解。我建议你把三角函数想象成圆上的坐标。单位圆上的点(x,y)，x就是cos，y就是sin。这样理解会直观很多。"),
    ("哦，这样啊。但是那些诱导公式太多了，根本记不住", "不要死记硬背！诱导公式都有规律：'奇变偶不变，符号看象限'。比如sin(π/2+α)，π/2是90度，是π/2的奇数倍，所以sin变cos，第二象限sin为正，所以结果是cosα。"),
    ("这个口诀我听过，但还是不太会用", "我们来练习一个：cos(π-α)等于什么？首先，π是180度，是π/2的偶数倍，所以cos不变还是cos；其次，π-α在第二象限，cos为负，所以结果是-cosα。你试试sin(3π/2+α)？"),
    ("让我想想...3π/2是270度，是π/2的奇数倍，sin要变成cos；3π/2+α在第四象限，sin为负，所以是-cosα？", "完全正确！你看，掌握方法后就不难了。关键是理解原理而不是死记。我们再练几个巩固一下。"),
    ("老师，我月考就要到了，除了三角函数还有函数图像变换也不会", "函数图像变换其实就是'平移'和'伸缩'。记住口诀：'左加右减，上加下减'。y=f(x-2)+3就是把原图像右移2单位，上移3单位。"),
    ("那y=2sin(2x+π/3)这种怎么变换？", "这涉及多个变换：1)2x使周期变为原来的1/2（横向压缩）2)+π/3使图像左移π/6（注意要除以x的系数2）3)前面的2使振幅变为2倍（纵向拉伸）。顺序很重要！"),
    ("太复杂了...有没有简单的记忆方法？", "有！按照'先相位后周期再振幅'的顺序：1)看x的整体（2x+π/3），左移π/6；2)看x的系数2，横向压缩1/2；3)看函数前的系数2，纵向拉伸2倍。画图时按这个顺序就不会乱。"),
    ("明白了一些。老师，我基础比较差，是不是应该多刷题？", "刷题要有方法！建议：1)先做课本例题，完全理解 2)分专题练习，比如这周只练三角函数 3)错题要整理分析，找出思维盲点 4)每天30分钟，坚持比突击有效。记住你是小明，基础需要慢慢补。"),
    ("我妈总说我笨，学不好数学", "不要这样想！每个人的学习节奏不同。你刚才能正确推导sin(3π/2+α)，说明你完全有能力学好。数学需要的是正确的方法和坚持练习，不是天赋。相信自己！"),
    ("谢谢老师的鼓励。我想问下，下次月考重点会考什么？", "根据高二进度，月考重点通常是：1)三角函数的图像和性质 2)三角恒等变换 3)解三角形（正弦定理、余弦定理）。你现在要重点突破三角函数基础，这是其他内容的基础。"),
    ("好的，我会努力的。对了老师，你上次说的那个学习方法是什么来着？", "你是指'先相位后周期再振幅'的图像变换顺序吗？还是指学习规划'每天30分钟分专题练习'？我刚才给你讲了好几个方法，你想复习哪个？"),
]

def create_conversation_messages(conversation_data: List[tuple]) -> List[BaseMessage]:
    """将对话数据转换为消息列表"""
    messages = []
    for human, ai in conversation_data:
        messages.append(HumanMessage(content=human))
        messages.append(AIMessage(content=ai))
    return messages

def print_strategy_comparison(strategy_name: str, original_count: int, final_count: int, 
                            final_messages: List[BaseMessage], execution_time: float):
    """美化打印策略对比结果"""
    print(f"\n{'='*60}")
    print(f"策略: {strategy_name}")
    print(f"执行时间: {execution_time:.2f}秒")
    print(f"原始消息数: {original_count} → 最终消息数: {final_count} (保留率: {final_count/original_count*100:.1f}%)")
    print(f"{'-'*60}")
    
    # 打印最终的消息内容
    for i, msg in enumerate(final_messages):
        msg_type = "系统" if isinstance(msg, SystemMessage) else "用户" if isinstance(msg, HumanMessage) else "助手"
        content = msg.content.replace('\n', ' ')
        
        # 特殊处理摘要消息
        if isinstance(msg, SystemMessage) and "【累积对话摘要" in msg.content:
            print(f"[{i+1}] 📝 摘要消息:")
            summary_content = msg.content.split('\n', 1)[1] if '\n' in msg.content else msg.content
            print(f"     {summary_content[:150]}...")
        else:
            # 限制每条消息显示长度
            display_content = content[:100] + "..." if len(content) > 100 else content
            icon = "👤" if msg_type == "用户" else "🤖" if msg_type == "助手" else "⚙️"
            print(f"[{i+1}] {icon} {msg_type}: {display_content}")

async def test_scenario(scenario_name: str, messages: List[BaseMessage], strategy_configs: Dict[str, Dict]):
    """测试单个场景"""
    print(f"\n{'#'*80}")
    print(f"# {scenario_name}")
    print(f"# 总消息数: {len(messages)} 条")
    print(f"{'#'*80}")
    
    # 初始化真实的LLM
    llm = init_llm()
    
    # 添加系统消息
    system_message = SystemMessage(content="你是一个专业的AI助手，请根据对话历史提供帮助。")
    full_messages = [system_message] + messages
    
    # 测试每个策略
    for strategy_name, config in strategy_configs.items():
        try:
            # 复制配置以避免修改原始字典
            config_copy = config.copy()
            
            # 创建策略实例
            strategy_type = config_copy.pop('type')
            if strategy_type == 'summary':
                config_copy['llm'] = llm
            
            strategy = create_memory_strategy(strategy_type, **config_copy)
            
            # 执行策略
            start_time = datetime.now()
            hook = strategy.create_pre_model_hook()
            state = {"messages": full_messages}
            result = hook(state)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            final_messages = result.get("llm_input_messages", [])
            
            # 打印结果
            print_strategy_comparison(
                strategy_name=strategy_name,
                original_count=len(full_messages),
                final_count=len(final_messages),
                final_messages=final_messages,
                execution_time=execution_time
            )
            
        except Exception as e:
            print(f"\n❌ 策略 {strategy_name} 执行失败: {str(e)}")
            import traceback
            traceback.print_exc()

async def main():
    """主测试函数"""
    print("🚀 开始测试不同记忆策略在真实场景下的表现")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 定义要测试的策略配置
    strategy_configs = {
        "无限制策略": {"type": "none"},
        "滑动窗口(10条)": {"type": "sliding_window", "max_messages": 10},
        "Token限制(50)": {"type": "token_limit", "max_tokens": 50},
        "自适应策略": {"type": "adaptive", "short_conversation_threshold": 10, "long_conversation_max_tokens": 200},
        "摘要策略": {"type": "summary", "keep_recent": 4, "checkpoint_interval": 8},
    }
    
    # 测试场景1：技术支持（20轮对话）
    tech_messages = create_conversation_messages(TECH_SUPPORT_CONVERSATION)
    await test_scenario("场景1: 技术支持对话", tech_messages, strategy_configs)
    
    # 测试场景2：产品咨询（24轮对话，包含大量细节）
    product_messages = create_conversation_messages(PRODUCT_CONSULTATION)
    await test_scenario("场景2: 产品咨询对话", product_messages, strategy_configs)
    
    # 测试场景3：学习辅导（26轮对话，需要记住学生特点）
    tutoring_messages = create_conversation_messages(TUTORING_CONVERSATION)
    await test_scenario("场景3: 学习辅导对话", tutoring_messages, strategy_configs)
    
    print("\n✅ 所有测试完成！")
    print("\n📊 测试总结：")
    print("- 无限制策略：保留所有上下文，适合短对话")
    print("- 滑动窗口：简单高效，但可能丢失重要早期信息")
    print("- Token限制：精确控制成本，但截断可能不够智能")
    print("- 自适应策略：平衡了短对话和长对话的需求")
    print("- 摘要策略：最适合长对话，能保留关键信息，但需要额外的LLM调用")

if __name__ == "__main__":
    asyncio.run(main())
