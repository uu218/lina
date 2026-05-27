import json
import csv
import os
from chains import EssayGraderPipeline

def main():
    print("🚀 初始化申论智能批改流水线...")
    
    try:
        pipeline = EssayGraderPipeline()
    except ValueError as e:
        print(e)
        return

    csv_file_path = "题目和参考答案22年国考地市卷.csv"
    
    if not os.path.exists(csv_file_path):
        print(f"❌ 找不到文件：{csv_file_path}")
        return

    print(f"📂 正在读取试卷数据: {csv_file_path}")
    
    all_evaluations = [] # 用于统一保存所有题目的批改结果
    
    with open(csv_file_path, 'r', encoding='gb18030') as f:
        reader = csv.DictReader(f)
        
        # 遍历 CSV 中的每一道题
        for index, row in enumerate(reader, 1):
            question_title = row.get('title', f'第{index}题')
            material_text = row.get('material', '无材料')
            answer_key1 = row.get('answer key1', '')
            answer_key2 = row.get('answer key2', '')
            
            # 读取新增的“我的作答”列。如果没有这一列或者内容为空，就跳过
            user_essay = row.get('我的作答', '').strip()
            
            print(f"\n" + "="*50)
            print(f"📝 开始处理: {question_title}")
            print(f"==================================================")

            if not user_essay:
                print("⚠️ 未检测到你的作答内容，已跳过该题。")
                continue

            agency_answers = f"【机构A参考答案】\n{answer_key1}\n\n【机构B参考答案】\n{answer_key2}"

            # 执行阶段 1
            print("⏳ [阶段 1] 提炼统一采分点大纲...")
            rubric = pipeline.run_stage1(
                question_text=question_title,
                material_text=material_text,
                agency_answers=agency_answers
            )

            # 执行阶段 2
            print("⏳ [阶段 2] 深度对标批改你的作答...")
            report = pipeline.run_stage2(
                unified_rubric=rubric,
                user_essay=user_essay
            )

            # 控制台即时反馈
            print("✅ 批改完成！")
            print(f"👉 最终得分: {report.total_score}")
            print(f"👉 全局总评: {report.summary_feedback}")
            
            # 将当前题目的结果存入列表
            all_evaluations.append({
                "题目序号": index,
                "题目": question_title,
                "采分点大纲": rubric.model_dump(),
                "最终批改报告": report.model_dump()
            })

    # 将所有题目的批改结果一次性保存为 JSON
    output_file = "evaluation_result_all.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_evaluations, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 完美！所有题目的评估结果已合并保存至 {output_file}")

if __name__ == "__main__":
    main()