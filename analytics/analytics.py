
"""Student-management analytics using NumPy, Pandas and scikit-learn.

The model is intentionally transparent: it estimates a student's academic-risk
score from attendance, GPA and outstanding-fee ratio. It is a data-science
component, not an automated disciplinary decision system.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

def build_student_risk_report(db_factory):
    with db_factory() as conn:
        rows=conn.execute("""
            SELECT s.id,s.registration_number,
                   s.first_name||' '||s.last_name AS student_name,
                   COALESCE(AVG(r.score),0) AS avg_score,
                   COALESCE(SUM(r.score*r.score*0),0) AS unused,
                   COALESCE(SUM(a.total_classes),0) AS total_classes,
                   COALESCE(SUM(a.classes_attended),0) AS classes_attended,
                   COALESCE(SUM(p.amount_due),0) AS amount_due,
                   COALESCE(SUM(p.amount_paid),0) AS amount_paid
            FROM students s
            LEFT JOIN results r ON r.student_id=s.id
            LEFT JOIN attendance a ON a.student_id=s.id
            LEFT JOIN payments p ON p.student_id=s.id
            GROUP BY s.id
            ORDER BY s.id
        """).fetchall()

    df=pd.DataFrame(rows)
    if df.empty:
        return {"model":"LogisticRegression","students":[],"summary":{"count":0}}

    # Avoid join multiplication affecting averages/sums by recomputing
    # student-level measures from independent SQL queries.
    with db_factory() as conn:
        res=pd.DataFrame(conn.execute("""
            SELECT student_id,AVG(score) avg_score,
                   SUM(CASE WHEN score>=50 THEN 1 ELSE 0 END)::float/NULLIF(COUNT(*),0) pass_rate
            FROM results GROUP BY student_id
        """).fetchall())
        att=pd.DataFrame(conn.execute("""
            SELECT student_id,SUM(classes_attended)::float/NULLIF(SUM(total_classes),0) attendance_rate
            FROM attendance GROUP BY student_id
        """).fetchall())
        pay=pd.DataFrame(conn.execute("""
            SELECT student_id,SUM(amount_due) due,SUM(amount_paid) paid
            FROM payments GROUP BY student_id
        """).fetchall())

    base=df[["id","registration_number","student_name"]].copy()
    for part in [res,att,pay]:
        if not part.empty: base=base.merge(part,left_on="id",right_on="student_id",how="left")
    for c in ["avg_score","pass_rate","attendance_rate","due","paid"]:
        if c not in base: base[c]=0.0
        base[c]=pd.to_numeric(base[c],errors="coerce").fillna(0.0)

    base["fee_balance_ratio"]=np.where(base["due"]>0,
                                        np.maximum(base["due"]-base["paid"],0)/base["due"],0)
    base["gpa_proxy"]=base["avg_score"]/20.0
    base["attendance_pct"]=base["attendance_rate"]*100

    X=base[["avg_score","attendance_pct","fee_balance_ratio"]].to_numpy(dtype=float)
    scaler=StandardScaler()
    Xs=scaler.fit_transform(X)

    # Build deterministic training labels from transparent thresholds so the
    # model can operate even when the database has only a few students.
    label=((base["avg_score"]<50) | (base["attendance_pct"]<75) |
           (base["fee_balance_ratio"]>0.5)).astype(int).to_numpy()
    if len(np.unique(label)) < 2:
        # Synthetic reference rows make the classifier trainable without
        # inventing student records.
        X_train=np.vstack([Xs,[-2,-2,1],[2,2,-1]])
        y_train=np.r_[label,1,0]
    else:
        X_train,y_train=Xs,label

    model=LogisticRegression(max_iter=1000,random_state=42)
    model.fit(X_train,y_train)
    probability=model.predict_proba(Xs)[:,1]

    base["risk_probability"]=np.round(probability,3)
    base["risk_band"]=np.where(base["risk_probability"]>=0.66,"High",
                         np.where(base["risk_probability"]>=0.33,"Medium","Low"))

    students=[]
    for _,r in base.iterrows():
        students.append({
            "id":int(r["id"]),
            "registration_number":r["registration_number"],
            "student_name":r["student_name"],
            "average_score":round(float(r["avg_score"]),2),
            "gpa_proxy":round(float(r["gpa_proxy"]),2),
            "attendance_percentage":round(float(r["attendance_pct"]),1),
            "outstanding_fee_ratio":round(float(r["fee_balance_ratio"]),2),
            "risk_probability":float(r["risk_probability"]),
            "risk_band":r["risk_band"]
        })
    return {
        "model":"LogisticRegression",
        "features":["average_score","attendance_percentage","outstanding_fee_ratio"],
        "students":students,
        "summary":{
            "count":len(students),
            "high":sum(x["risk_band"]=="High" for x in students),
            "medium":sum(x["risk_band"]=="Medium" for x in students),
            "low":sum(x["risk_band"]=="Low" for x in students)
        }
    }
