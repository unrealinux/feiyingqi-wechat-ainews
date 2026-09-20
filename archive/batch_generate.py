"""批量生成所有13篇AI工具横评文章并发布到微信草稿箱"""
import subprocess
import time

article_types = [
    "meeting_tools_review",
    "image_tools_review", 
    "note_tools_review",  # 已生成
    "search_tools_review",
    "code_tools_review",
    "video_tools_review",
    "audio_tools_review",
    "office_tools_review",
    "design_tools_review",
    "marketing_tools_review",
    "data_tools_review",
    "education_tools_review",
    "medical_tools_review",
    "finance_tools_review",
    "legal_tools_review"
]

print(f"开始批量生成 {len(article_types)} 篇文章...\n")

success_count = 0
failed_types = []

for i, article_type in enumerate(article_types, 1):
    print(f"\n[{i}/{len(article_types)}] 生成 {article_type}...")
    
    try:
        result = subprocess.run(
            ["python", "main.py", "custom-article", "--type", article_type, "--publish"],
            cwd=r"E:\Project\feiyingqi-wechat-ainews",
            capture_output=True,
            text=True,
            timeout=180  # 3分钟超时
        )
        
        if "SUCCESS" in result.stdout or "已发布到微信草稿箱" in result.stdout:
            print(f"   [成功]")
            success_count += 1
        else:
            print(f"   [失败]")
            print(f"   错误: {result.stderr[-200:] if result.stderr else result.stdout[-200:]}")
            failed_types.append(article_type)
        
        # 避免API限流，等待几秒
        if i < len(article_types):
            time.sleep(5)
            
    except subprocess.TimeoutExpired:
        print(f"   [超时]")
        failed_types.append(article_type)
    except Exception as e:
        print(f"   [异常: {e}]")
        failed_types.append(article_type)

print(f"\n{'='*50}")
print(f"批量生成完成！")
print(f"成功: {success_count}/{len(article_types)}")
if failed_types:
    print(f"失败类型: {', '.join(failed_types)}")
print(f"请登录 https://mp.weixin.qq.com 查看草稿箱")
print(f"{'='*50}")
