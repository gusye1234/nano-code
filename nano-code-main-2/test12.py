import asyncio
import json
from nanocode1.final_launch import Coding_agent
from nanocode1.models.dissertation_plan import DissertationPlan
from nanocode1.models import ReportModel

async def main():
    agent = Coding_agent(working_dir="/Users/gengjiawei/Desktop/testdir")
    plan = DissertationPlan.from_file("/Users/gengjiawei/Documents/coding/nano-code-main-2/Json—test/test_plan.json")
    reportorplan = await agent.generate_report(plan)

    if isinstance(reportorplan, DissertationPlan):
        # 输出更新后的dissertation plan
        print(json.dumps(reportorplan.model_dump(), ensure_ascii=False, indent=2))

asyncio.run(main())