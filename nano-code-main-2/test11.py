import asyncio
import json
from nanocode1.final_launch import Coding_agent
from nanocode1.models.dissertation_plan import DissertationPlan
from nanocode1.models import ReportModel

async def main():
    agent = Coding_agent(working_dir="/Users/gengjiawei/Desktop/testdir")
    plan = DissertationPlan.from_file("/Users/gengjiawei/Documents/coding/nano-code-main-2/Json—test/result_1756975300.8282976.json")
    existing_report = None  # 没有现有报告时传递 None

    #existing_report = ReportModel.from_file("/Users/gengjiawei/Desktop/testdir/agent_output.json")
    # 传入plan和已有的report_model
    reportorplan = await agent.generate_report(plan, existing_report)

    if isinstance(reportorplan, DissertationPlan):
        print(json.dumps(reportorplan.model_dump(), ensure_ascii=False, indent=2))
    elif isinstance(reportorplan, ReportModel):
        print(json.dumps(reportorplan.model_dump(), ensure_ascii=False, indent=2))

asyncio.run(main())

