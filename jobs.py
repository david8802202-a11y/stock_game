"""職業定義 - MVP 先放 1 個 (工程師),架構支援多職業擴充"""

JOBS = {
    "engineer": {
        "name": "軟體工程師",
        "desc": "穩定高薪,但常加班、缺乏運動",
        "starting_salary": 55000,        # 月薪
        "starting_cash": 100000,         # 起始現金
        "starting_expense": 22000,       # 月固定支出 (房租+水電+伙食)
        "salary_growth_yearly": 0.04,    # 每年加薪 4%
        "promotion_chance": 0.15,        # 每季升職機率 (skill > 70 時觸發)
        
        "starting_stats": {
            "health": 75,    # 健康
            "mood": 70,      # 心情
            "skill": 55,     # 技能
            "social": 40,    # 人脈
        },
        
        # 月初固定變化 (久坐工作健康會掉、加班心情會差)
        "monthly_stat_drift": {
            "health": -1,
            "mood": -1,
            "skill": +1,
            "social": -1,
        },
        
        # 此職業特有的事件權重加成
        "event_modifiers": {
            "back_pain": 2.0,           # 背痛 2 倍機率
            "eye_strain": 2.0,          # 眼睛 2 倍機率
            "overtime_bonus": 1.5,      # 加班獎金多
            "tech_layoff": 1.5,         # 科技業裁員
        },
    },
}


def get_job(job_id):
    return JOBS.get(job_id, JOBS["engineer"])
