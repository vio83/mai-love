from __future__ import annotations

import json
import threading
import time
import hashlib
from pathlib import Path
from typing import Any


class EnterpriseStrategy:
    """Customer, moat, compliance, and go-to-market foundation for production use."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.audit_path = project_root / "data" / "logs" / "enterprise_audit.jsonl"
        self.design_partners_path = project_root / "data" / "config" / "design_partners.json"
        self.customer_profiles_path = project_root / "data" / "config" / "customer_profiles.json"
        self.tenant_policies_path = project_root / "data" / "config" / "tenant_policies.json"
        self._lock = threading.Lock()

        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        self.design_partners_path.parent.mkdir(parents=True, exist_ok=True)
        self.customer_profiles_path.parent.mkdir(parents=True, exist_ok=True)
        self.tenant_policies_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.design_partners_path.exists():
            self.design_partners_path.write_text(
                json.dumps({"partners": [], "updated_at": self._now_iso()}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        if not self.customer_profiles_path.exists():
            self.customer_profiles_path.write_text(
                json.dumps({"customers": [], "updated_at": self._now_iso()}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        if not self.tenant_policies_path.exists():
            self.tenant_policies_path.write_text(
                json.dumps({"tenants": {}, "updated_at": self._now_iso()}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        self.positioning = "AI orchestration privacy-first per team regolati EU"

        self.customer_profile = {
            "icp": {
                "segments": [
                    "PMI e studi professionali EU regolati",
                    "Healthcare operativo, legale, finance ops, consulenza",
                    "Team con dati sensibili e bisogno di auditability",
                ],
                "buying_triggers": [
                    "Necessita data resncy e controllo locale/ibrido",
                    "Richiesta tracciabilita completa delle decisioni AI",
                    "Riduzione rischio compliance con policy enforceable",
                ],
                "pain_points": [
                    "AI cloud-only non conforme a policy interne",
                    "Nessun controllo centralizzato del routing modelli",
                    "Mancanza audit trail utile in verifiche legali",
                ],
            },
            "value_proposition": "Riduci rischio compliance e costo operativo con orchestrazione AI governata e verificabile.",
            "moat": [
                "Policy routing basato su classificazione dati",
                "Audit trail immutabile di richieste e decisioni",
                "Preset verticali regolati e workflow proprietari",
            ],
        }

        self.pricing = {
            "currency": "EUR",
            "plans": [
                {"id": "starter", "price_month": 99, "seat_included": 5, "features": ["local-first", "base audit", "basic routing"]},
                {"id": "pro", "price_month": 299, "seat_included": 20, "features": ["policy engine", "rbac", "compliance routing"]},
                {"id": "enterprise", "price_month": 999, "seat_included": 100, "features": ["advanced audit", "custom policy", "private deployment"]},
            ],
        }

        self.metrics = {
            "north_star": "weekly_active_teams",
            "core": [
                "design_partners_paid",
                "task_time_reduction_percent",
                "regulated_workflows_completed",
                "compliance_policy_block_rate",
                "monthly_churn_percent",
            ],
            "targets_90_days": {
                "design_partners_paid": 10,
                "task_time_reduction_percent": 30,
                "monthly_churn_percent": 8,
            },
        }

        self.go_no_go = {
            "go": [
                ">=10 design partner paganti",
                "Riduzione tempo task >=30%",
                "0 incnti critici su dati sensibili",
            ],
            "no_go": [
                "<3 clienti paganti in 90 giorni",
                "Nessun vantaggio misurabile vs tool cloud generici",
                "Mancata adozione dei preset compliance",
            ],
        }

        self.roadmap = [
            {
                "phase": "0-30 giorni",
                "focus": "Market fit + compliance core",
                "deliverables": [
                    "Onboarding ICP e segmentazione customer",
                    "Policy routing v1 + audit trail v1",
                    "RBAC baseline e design partner pipeline",
                ],
            },
            {
                "phase": "31-60 giorni",
                "focus": "Reasoning orchestrato + agent autonomy controllata",
                "deliverables": [
                    "Reasoning plan-execute-verify con fallback",
                    "Agent loop con approvazione umana",
                    "Runbook verticali per use case regolati",
                ],
            },
            {
                "phase": "61-90 giorni",
                "focus": "Vision + voice + go-to-market scaling",
                "deliverables": [
                    "Vision su documenti per workflow verticali",
                    "Voice end-to-end con policy enforcement",
                    "3 use case verticali pubblici + SDK/plugin beta",
                ],
            },
        ]

        self.rbac_permissions = {
            "owner": {"strategy:write", "strategy:read", "audit:read", "policy:write", "policy:read", "partner:write", "partner:read"},
            "admin": {"strategy:read", "audit:read", "policy:write", "policy:read", "partner:write", "partner:read"},
            "analyst": {"strategy:read", "audit:read", "policy:read", "partner:read"},
            "viewer": {"strategy:read", "policy:read"},
        }

        self.policy_presets = {
            "legal": {
                "name": "Legal EU",
                "jurisdiction": "eu",
                "sensitive_data_policy": "force_local",
                "allowed_cloud_for_public": ["claude", "openai", "gemini"],
                "required_audit_level": "full",
            },
            "fiscal": {
                "name": "Fiscal & Accounting",
                "jurisdiction": "eu",
                "sensitive_data_policy": "force_local",
                "allowed_cloud_for_public": ["claude", "openai"],
                "required_audit_level": "full",
            },
            "healthcare": {
                "name": "Healthcare Ops",
                "jurisdiction": "eu",
                "sensitive_data_policy": "force_local",
                "allowed_cloud_for_public": ["claude", "gemini"],
                "required_audit_level": "strict",
            },
            "finance_ops": {
                "name": "Finance Ops",
                "jurisdiction": "eu",
                "sensitive_data_policy": "force_local",
                "allowed_cloud_for_public": ["claude", "openai", "mistral"],
                "required_audit_level": "full",
            },
            "generic_eu": {
                "name": "Generic Regulated EU",
                "jurisdiction": "eu",
                "sensitive_data_policy": "force_local",
                "allowed_cloud_for_public": ["claude", "openai", "gemini", "mistral"],
                "required_audit_level": "standard",
            },
        }

        self.plan_guardrails = {
            "free_local": {
                "max_tokens": 2048,
                "max_team_members": 1,
                "allow_cloud": False,
                "allow_vision": False,
                "allow_voice": True,
            },
            "starter": {
                "max_tokens": 4096,
                "max_team_members": 5,
                "allow_cloud": True,
                "allow_vision": False,
                "allow_voice": True,
            },
            "pro": {
                "max_tokens": 8192,
                "max_team_members": 20,
                "allow_cloud": True,
                "allow_vision": True,
                "allow_voice": True,
            },
            "premium": {
                "max_tokens": 16384,
                "max_team_members": 50,
                "allow_cloud": True,
                "allow_vision": True,
                "allow_voice": True,
            },
            "enterprise": {
                "max_tokens": 32768,
                "max_team_members": 500,
                "allow_cloud": True,
                "allow_vision": True,
                "allow_voice": True,
            },
        }

    def _now_iso(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def classify_data(self, text: str, has_images: bool = False) -> str:
        payload = (text or "").lower()
        restricted_keywords = [
            "health", "medical", "patient", "diagnosi", "sanitario", "iban", "passport", "ssn", "fiscale",
            "credito", "payment", "password", "token", "chiave api", "api key",
        ]
        confidential_keywords = ["contract", "nda", "bilancio", "invoice", "stipendio", "employee", "cliente", "customer"]

        if any(k in payload for k in restricted_keywords):
            return "restricted"
        if any(k in payload for k in confidential_keywords):
            return "confidential"
        if has_images:
            return "internal"
        return "public"

    def route_request(
        self,
        mode: str,
        provider: str | None,
        classification: str,
        jurisdiction: str = "eu",
        policy_preset: str = "generic_eu",
        tenant_policy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        requested_mode = mode or "local"
        requested_provr = provider or ("ollama" if requested_mode == "local" else "claude")

        reason = "allowed"
        effective_mode = requested_mode
        effective_provr = requested_provr
        cloud_allowed = True
        preset = self.policy_presets.get(policy_preset, self.policy_presets["generic_eu"])
        allowed_cloud_for_public = set(preset.get("allowed_cloud_for_public", []))

        if tenant_policy and tenant_policy.get("data_resncy") in {"local-only", "eu-only"} and requested_mode == "cloud":
            cloud_allowed = False
            effective_mode = "local"
            effective_provr = "ollama"
            reason = "tenant-data-resncy-forced-local"

        if classification in {"restricted", "confidential"}:
            cloud_allowed = False
            effective_mode = "local"
            effective_provr = "ollama"
            reason = "forced-local-sensitive-data"

        if jurisdiction.lower() in {"eu", "it"} and classification == "internal" and requested_mode == "cloud":
            reason = "eu-internal-cloud-review-required"

        if classification == "public" and cloud_allowed and effective_mode == "cloud":
            if allowed_cloud_for_public and effective_provr not in allowed_cloud_for_public:
                effective_provr = next(iter(allowed_cloud_for_public))
                reason = "preset-adjusted-provider"

        return {
            "classification": classification,
            "jurisdiction": jurisdiction,
            "policy_preset": policy_preset,
            "requested": {"mode": requested_mode, "provider": requested_provr},
            "effective": {"mode": effective_mode, "provider": effective_provr},
            "cloud_allowed": cloud_allowed,
            "reason": reason,
        }

    def list_policy_presets(self) -> dict[str, Any]:
        return self.policy_presets

    def get_plan_guardrails(self) -> dict[str, Any]:
        return self.plan_guardrails

    def enforce_plan_guardrails(self, plan_id: str, mode: str, max_tokens: int, feature: str = "chat") -> dict[str, Any]:
        guard = self.plan_guardrails.get(plan_id, self.plan_guardrails["free_local"])
        requested_mode = mode or "local"
        effective_mode = requested_mode
        reason = "ok"

        if requested_mode == "cloud" and not guard.get("allow_cloud", False):
            effective_mode = "local"
            reason = "plan-forces-local"

        if feature == "vision" and not guard.get("allow_vision", False):
            reason = "plan-does-not-allow-vision"

        effective_max_tokens = min(max(64, int(max_tokens)), int(guard.get("max_tokens", 2048)))

        return {
            "plan_id": plan_id,
            "requested_mode": requested_mode,
            "effective_mode": effective_mode,
            "requested_max_tokens": max_tokens,
            "effective_max_tokens": effective_max_tokens,
            "reason": reason,
            "guardrails": guard,
        }

    def has_permission(self, role: str, permission: str) -> bool:
        normalized = (role or "viewer").strip().lower()
        return permission in self.rbac_permissions.get(normalized, set())

    def write_audit_event(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {
            "timestamp": self._now_iso(),
            "event_type": event_type,
            "payload": payload,
        }
        line = json.dumps(event, ensure_ascii=False)
        with self._lock:
            with self.audit_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

    def read_recent_audit(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.audit_path.exists():
            return []

        rows = self.audit_path.read_text(encoding="utf-8").splitlines()
        selected = rows[-max(1, min(limit, 500)):]
        out: list[dict[str, Any]] = []
        for row in selected:
            try:
                out.append(json.loads(row))
            except Exception:
                continue
        return out

    def export_audit(self, format_name: str = "json") -> dict[str, Any]:
        events = self.read_recent_audit(limit=500)
        normalized = (format_name or "json").strip().lower()
        if normalized == "jsonl":
            payload = "\n".join(json.dumps(e, ensure_ascii=False) for e in events)
            return {"format": "jsonl", "content": payload, "count": len(events)}
        return {"format": "json", "content": events, "count": len(events)}

    def list_customer_profiles(self) -> dict[str, Any]:
        try:
            data = json.loads(self.customer_profiles_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {"customers": [], "updated_at": self._now_iso()}
            data.setdefault("customers", [])
            data.setdefault("updated_at", self._now_iso())
            return data
        except Exception:
            return {"customers": [], "updated_at": self._now_iso()}

    def list_tenant_policies(self) -> dict[str, Any]:
        try:
            data = json.loads(self.tenant_policies_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {"tenants": {}, "updated_at": self._now_iso()}
            data.setdefault("tenants", {})
            data.setdefault("updated_at", self._now_iso())
            return data
        except Exception:
            return {"tenants": {}, "updated_at": self._now_iso()}

    def get_tenant_policy(self, tenant_id: str) -> dict[str, Any]:
        data = self.list_tenant_policies()
        tenants = data.get("tenants", {})
        policy = tenants.get(tenant_id, {}) if isinstance(tenants, dict) else {}
        if not policy:
            policy = {
                "tenant_id": tenant_id,
                "policy_preset": "generic_eu",
                "jurisdiction": "eu",
                "data_resncy": "eu-only",
                "updated_at": self._now_iso(),
            }
        return policy

    def set_tenant_policy(
        self,
        tenant_id: str,
        policy_preset: str,
        jurisdiction: str,
        data_resncy: str,
    ) -> dict[str, Any]:
        tenant_norm = (tenant_id or "").strip()
        preset_norm = (policy_preset or "").strip().lower()
        jurisdiction_norm = (jurisdiction or "eu").strip().lower()
        resncy_norm = (data_resncy or "eu-only").strip().lower()

        if not tenant_norm:
            raise ValueError("tenant_id obbligatorio")
        if preset_norm not in self.policy_presets:
            raise ValueError("policy_preset non valido")
        if resncy_norm not in {"local-only", "eu-only", "global"}:
            raise ValueError("data_resncy non valida")

        data = self.list_tenant_policies()
        tenants = data.get("tenants", {})
        if not isinstance(tenants, dict):
            tenants = {}

        policy = {
            "tenant_id": tenant_norm,
            "policy_preset": preset_norm,
            "jurisdiction": jurisdiction_norm,
            "data_resncy": resncy_norm,
            "updated_at": self._now_iso(),
        }
        tenants[tenant_norm] = policy
        data["tenants"] = tenants
        data["updated_at"] = self._now_iso()
        self.tenant_policies_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return policy

    def onboarding_customer(
        self,
        company: str,
        contact_email: str,
        segment: str,
        policy_preset: str,
        plan_id: str,
        use_case: str,
    ) -> dict[str, Any]:
        company_norm = (company or "").strip()
        email_norm = (contact_email or "").strip().lower()
        segment_norm = (segment or "").strip().lower()
        preset_norm = (policy_preset or "").strip().lower()
        plan_norm = (plan_id or "").strip().lower()
        use_case_norm = (use_case or "").strip()

        allowed_segments = {"legal", "fiscal", "healthcare", "finance_ops", "generic_eu"}
        if segment_norm not in allowed_segments:
            raise ValueError("segment non valido")
        if preset_norm not in self.policy_presets:
            raise ValueError("policy_preset non valido")
        if plan_norm not in self.plan_guardrails:
            raise ValueError("plan_id non valido")
        if not company_norm or "@" not in email_norm:
            raise ValueError("company e contact_email validi sono obbligatori")
        if not use_case_norm:
            raise ValueError("use_case obbligatorio")

        data = self.list_customer_profiles()
        customers = data.get("customers", [])
        if any((c.get("contact_email", "").lower() == email_norm) for c in customers if isinstance(c, dict)):
            raise ValueError("contact_email gia onboarding")

        customer = {
            "customer_id": f"cust-{int(time.time())}",
            "company": company_norm,
            "contact_email": email_norm,
            "segment": segment_norm,
            "policy_preset": preset_norm,
            "plan_id": plan_norm,
            "use_case": use_case_norm,
            "status": "onboarded",
            "created_at": self._now_iso(),
        }
        customers.append(customer)
        data["customers"] = customers
        data["updated_at"] = self._now_iso()
        self.customer_profiles_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        return customer

    def compute_roi_dashboard(self, days: int, metrics_summary: dict[str, Any]) -> dict[str, Any]:
        totals = metrics_summary.get("totals", {}) if isinstance(metrics_summary, dict) else {}
        total_calls = int(totals.get("total_calls", 0) or 0)
        avg_latency = float(totals.get("avg_latency", 0) or 0)
        token_total = int(totals.get("total_tokens", 0) or 0)

        baseline_minutes_per_task = 12.0
        ai_minutes_per_task = 8.0
        if total_calls > 0 and avg_latency > 0:
            ai_minutes_per_task = max(3.0, min(11.0, 6.0 + (avg_latency / 4000.0)))

        saved_minutes = max(0.0, (baseline_minutes_per_task - ai_minutes_per_task) * total_calls)
        saved_hours = round(saved_minutes / 60.0, 2)
        estimated_cost_avod_eur = round(saved_hours * 42.0, 2)
        risk_reduction_score = min(100, 20 + int(total_calls / 10) + (8 if token_total > 100000 else 0))

        return {
            "period_days": days,
            "workload": {
                "total_calls": total_calls,
                "total_tokens": token_total,
                "avg_latency_ms": round(avg_latency, 1),
            },
            "roi": {
                "estimated_time_saved_hours": saved_hours,
                "estimated_cost_avod_eur": estimated_cost_avod_eur,
                "estimated_task_time_reduction_percent": round(max(0.0, (saved_minutes / max(1.0, baseline_minutes_per_task * max(1, total_calls))) * 100.0), 1),
                "estimated_risk_reduction_score": risk_reduction_score,
            },
            "targets": {
                "time_reduction_target_percent": self.metrics["targets_90_days"]["task_time_reduction_percent"],
                "churn_target_percent": self.metrics["targets_90_days"]["monthly_churn_percent"],
            },
        }

    def list_design_partners(self) -> dict[str, Any]:
        try:
            data = json.loads(self.design_partners_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {"partners": [], "updated_at": self._now_iso()}
            data.setdefault("partners", [])
            data.setdefault("updated_at", self._now_iso())
            return data
        except Exception:
            return {"partners": [], "updated_at": self._now_iso()}

    def add_design_partner(self, company: str, contact_email: str, segment: str, notes: str = "") -> dict[str, Any]:
        company_norm = (company or "").strip()
        email_norm = (contact_email or "").strip().lower()
        segment_norm = (segment or "").strip()

        if not company_norm or not email_norm or "@" not in email_norm:
            raise ValueError("company e contact_email validi sono obbligatori")

        data = self.list_design_partners()
        partners = data.get("partners", [])
        if any((p.get("contact_email", "").lower() == email_norm) for p in partners if isinstance(p, dict)):
            raise ValueError("contact_email gia presente")

        partner = {
            "partner_id": f"dp-{hashlib.blake2s(email_norm.encode('utf-8'), digest_size=6).hexdigest()}",
            "company": company_norm,
            "contact_email": email_norm,
            "segment": segment_norm or "regulated-eu",
            "notes": notes.strip(),
            "added_at": self._now_iso(),
            "status": "prospect",
            "monthly_ticket_eur": 0,
        }
        partners.append(partner)
        data["partners"] = partners
        data["updated_at"] = self._now_iso()

        self.design_partners_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return partner

    def update_design_partner_status(self, partner_id: str, status: str, monthly_ticket_eur: int = 0) -> dict[str, Any]:
        allowed = {"prospect", "pilot", "paid", "churned"}
        status_norm = (status or "").strip().lower()
        partner_norm = (partner_id or "").strip()
        if status_norm not in allowed:
            raise ValueError("status non valido")
        if not partner_norm:
            raise ValueError("partner_id obbligatorio")

        data = self.list_design_partners()
        partners = data.get("partners", [])
        found: dict[str, Any] | None = None
        for p in partners:
            if isinstance(p, dict) and p.get("partner_id") == partner_norm:
                p["status"] = status_norm
                p["monthly_ticket_eur"] = max(0, int(monthly_ticket_eur or p.get("monthly_ticket_eur", 0)))
                p["status_updated_at"] = self._now_iso()
                found = p
                break

        if not found:
            raise ValueError("partner_id non trovato")

        data["partners"] = partners
        data["updated_at"] = self._now_iso()
        self.design_partners_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return found

    def design_partner_funnel(self) -> dict[str, Any]:
        data = self.list_design_partners()
        partners = [p for p in data.get("partners", []) if isinstance(p, dict)]

        total = len(partners)
        prospect = sum(1 for p in partners if p.get("status") == "prospect")
        pilot = sum(1 for p in partners if p.get("status") == "pilot")
        paid = sum(1 for p in partners if p.get("status") == "paid")
        churned = sum(1 for p in partners if p.get("status") == "churned")

        pilot_to_paid = (paid / pilot) if pilot > 0 else 0.0
        churn_rate = (churned / max(1, paid + churned)) * 100.0
        mrr = sum(int(p.get("monthly_ticket_eur", 0) or 0) for p in partners if p.get("status") == "paid")

        return {
            "total": total,
            "prospect": prospect,
            "pilot": pilot,
            "paid": paid,
            "churned": churned,
            "pilot_to_paid_rate": round(pilot_to_paid, 3),
            "monthly_churn_percent": round(churn_rate, 2),
            "mrr_eur": mrr,
            "targets": {
                "paid_target_90d": self.metrics["targets_90_days"]["design_partners_paid"],
                "max_churn_percent": self.metrics["targets_90_days"]["monthly_churn_percent"],
            },
        }


_ENTERPRISE_STRATEGY: EnterpriseStrategy | None = None


def get_enterprise_strategy(project_root: Path) -> EnterpriseStrategy:
    global _ENTERPRISE_STRATEGY
    if _ENTERPRISE_STRATEGY is None:
        _ENTERPRISE_STRATEGY = EnterpriseStrategy(project_root=project_root)
    return _ENTERPRISE_STRATEGY
