from __future__ import annotations

import csv
from datetime import datetime
from io import BytesIO, StringIO

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from VecInsurance import VehicleDataError, VehicleInsuranceManager


app = Flask(__name__)
app.secret_key = "vehicle-insurance-demo-key"


def to_bool(raw: str) -> bool:
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


@app.get("/")
def index():
    try:
        manager = VehicleInsuranceManager()
        q = request.args.get("q", "").strip()
        
        if q:
            policies = manager.search_policies(q)
            claims = manager.search_claims(q)
        else:
            policies = manager.get_policies()
            claims = manager.get_claims()
            
        analysis = manager.get_premium_analysis()
        has_analysis = analysis is not None and not analysis.empty
        return render_template(
            "index.html",
            policies=policies,
            claims=claims,
            has_analysis=has_analysis,
            search_query=q,
        )
    except Exception as exc:
        flash(f"Startup error: {exc}", "error")
        return render_template("index.html", policies=[], claims=[], has_analysis=False)


@app.get("/analysis/premium-chart")
def premium_chart():
    try:
        manager = VehicleInsuranceManager()
        fig = manager.plot_premium_distribution()
        if fig is None:
            flash("No data available for analysis.", "error")
            return redirect(url_for("index"))

        image_io = BytesIO()
        fig.savefig(image_io, format="png", bbox_inches="tight")
        plt.close(fig)
        image_io.seek(0)
        return send_file(image_io, mimetype="image/png")
    except Exception as exc:
        flash(f"Analysis failed: {exc}", "error")
        return redirect(url_for("index"))


@app.get("/analysis/premium-bar")
def premium_bar_chart():
    try:
        manager = VehicleInsuranceManager()
        analysis = manager.get_premium_analysis()
        if analysis is None or analysis.empty:
            flash("No data available for analysis.", "error")
            return redirect(url_for("index"))

        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        ax.bar(analysis.index.astype(str), analysis.values)
        ax.set_title("Average Premium by Vehicle Type")
        ax.set_xlabel("Vehicle Type")
        ax.set_ylabel("Average Premium")
        ax.tick_params(axis="x", rotation=15)
        fig.tight_layout()

        image_io = BytesIO()
        fig.savefig(image_io, format="png", bbox_inches="tight")
        plt.close(fig)
        image_io.seek(0)
        return send_file(image_io, mimetype="image/png")
    except Exception as exc:
        flash(f"Analysis failed: {exc}", "error")
        return redirect(url_for("index"))
def rows_to_csv_bytes(headers: list[str], rows: list[tuple]) -> BytesIO:
    text_io = StringIO()
    writer = csv.writer(text_io)
    writer.writerow(headers)
    writer.writerows(rows)
    data = BytesIO(text_io.getvalue().encode("utf-8"))
    data.seek(0)
    return data


@app.get("/download/policies.csv")
def download_policies_csv():
    manager = VehicleInsuranceManager()
    rows = manager.get_policies()
    headers = [
        "id",
        "owner_name",
        "vehicle_type",
        "engine_cc",
        "model_year",
        "base_value",
        "premium",
        "risk_score",
        "is_commercial",
        "start_date",
        "expiry_date",
    ]
    data = rows_to_csv_bytes(headers, rows)
    return send_file(data, mimetype="text/csv", as_attachment=True, download_name="policies.csv")


@app.get("/download/claims.csv")
def download_claims_csv():
    manager = VehicleInsuranceManager()
    rows = manager.get_claims()
    headers = ["id", "policy_id", "damage_cost", "incident_type", "claim_status"]
    data = rows_to_csv_bytes(headers, rows)
    return send_file(data, mimetype="text/csv", as_attachment=True, download_name="claims.csv")


@app.post("/policy/create")
def create_policy():
    try:
        manager = VehicleInsuranceManager()
        owner = request.form.get("owner", "")
        v_type = request.form.get("vehicle_type", "")
        cc = int(request.form.get("engine_cc", "0"))
        year = int(request.form.get("model_year", "0"))
        value = float(request.form.get("market_value", "0"))
        
        start_date_str = request.form.get("start_date", "").strip()
        expiry_date_str = request.form.get("expiry_date", "").strip()
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        
        is_commercial = to_bool(request.form.get("is_commercial", "0"))
        
        if is_commercial:
            load_capacity_str = request.form.get("load_capacity", "").strip()
            load_capacity = float(load_capacity_str) if load_capacity_str else None
        else:
            load_capacity = None
            
        result = manager.create_policy(
            owner=owner,
            v_type=v_type,
            cc=cc,
            year=year,
            value=value,
            start_date=start_date,
            expiry_date=expiry_date,
            is_commercial=is_commercial,
            load_capacity=load_capacity,
        )
        flash(
            f"Policy created: ID {result['policy_id']} | Valid for {result['months']} months | Premium ${result['premium']}",
            "success",
        )
    except VehicleDataError as exc:
        flash(str(exc), "error")
    except Exception as exc:
        flash(f"Create failed: {exc}", "error")
    return redirect(url_for("index"))
@app.post("/policy/update")
def update_policy():
    try:
        manager = VehicleInsuranceManager()
        pid = int(request.form.get("policy_id", "0"))
        owner = request.form.get("owner", "") or None
        v_type = request.form.get("vehicle_type", "") or None
        
        cc_str = request.form.get("engine_cc", "").strip()
        cc = int(cc_str) if cc_str else None
        
        year_str = request.form.get("model_year", "").strip()
        year = int(year_str) if year_str else None
        
        val_str = request.form.get("market_value", "").strip()
        value = float(val_str) if val_str else None
        
        start_date_str = request.form.get("start_date", "").strip()
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        
        expiry_date_str = request.form.get("expiry_date", "").strip()
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date() if expiry_date_str else None
        
        is_comm_str = request.form.get("is_commercial", "").strip()
        is_commercial = to_bool(is_comm_str) if is_comm_str else None
        
        load_capacity_str = request.form.get("load_capacity", "").strip()
        load_capacity = float(load_capacity_str) if load_capacity_str else None
            
        result = manager.update_policy(
            pid=pid,
            owner=owner,
            v_type=v_type,
            cc=cc,
            year=year,
            value=value,
            start_date=start_date,
            expiry_date=expiry_date,
            is_commercial=is_commercial,
            load_capacity=load_capacity,
        )
        flash(
            f"Policy updated: ID {result['policy_id']} | Valid for {result['months']} months | Premium ${result['premium']}",
            "success",
        )
    except VehicleDataError as exc:
        flash(str(exc), "error")
    except Exception as exc:
        flash(f"Update failed: {exc}", "error")
    return redirect(url_for("index"))
@app.post("/policy/delete")
def delete_policy():
    try:
        manager = VehicleInsuranceManager()
        pid = int(request.form.get("policy_id", "0"))
        manager.delete_policy(pid)
        flash(f"Policy deleted: ID {pid}", "success")
    except VehicleDataError as exc:
        flash(str(exc), "error")
    except Exception as exc:
        flash(f"Delete failed: {exc}", "error")
    return redirect(url_for("index"))
@app.post("/claim/create")
def create_claim():
    try:
        manager = VehicleInsuranceManager()
        pid = int(request.form.get("policy_id", "0"))
        damage = float(request.form.get("damage_cost", "0"))
        incident = request.form.get("incident_type", "")
        status = manager.submit_claim(pid=pid, damage=damage, incident=incident.lower())
        flash(f"Claim submitted: {status}", "success")
    except VehicleDataError as exc:
        flash(str(exc), "error")
    except Exception as exc:
        flash(f"Claim failed: {exc}", "error")
    return redirect(url_for("index"))
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)