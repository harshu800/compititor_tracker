export type PageType = "homepage" | "pricing" | "features" | "product" | "changelog" | "blog" | "custom";
export type CheckFrequency = "daily" | "weekly";
export type Importance = "critical" | "high" | "medium" | "low";
export type ChangeType =
  | "pricing" | "feature" | "positioning" | "product" | "offer"
  | "cta" | "content" | "messaging" | "legal" | "design" | "other";
export type ReviewStatus = "unread" | "reviewed" | "important" | "ignored";

export interface Organization {
  id: string;
  name: string;
  role: "owner" | "admin" | "member";
  plan: "free" | "pro" | "business";
}

export interface Competitor {
  id: string;
  name: string;
  website_url: string;
  description: string | null;
  industry: string | null;
  logo_url: string | null;
  status: "active" | "archived";
  created_at: string;
}

export interface MonitoredPage {
  id: string;
  url: string;
  page_type: PageType;
  name: string | null;
  monitoring_enabled: boolean;
  check_frequency: CheckFrequency;
  last_checked_at: string | null;
  last_changed_at: string | null;
  last_status_code: string | null;
}

export interface Change {
  id: string;
  monitored_page_id: string;
  change_type: ChangeType;
  importance: Importance;
  impact_score: number;
  summary: string | null;
  what_changed: string | null;
  why_it_matters: string | null;
  recommended_action: string | null;
  ai_confidence: number | null;
  diff_json: {
    added: string[];
    removed: string[];
    modified: { before: string; after: string }[];
    structured_changes: Record<string, unknown>;
    change_score: number;
  } | null;
  review_status: ReviewStatus;
  created_at: string;
}

export interface DashboardData {
  competitors: number;
  changes_this_week: number;
  important_changes: number;
  unreviewed: number;
  recent_important_changes: {
    change_id: string;
    competitor_name: string;
    change_type: ChangeType;
    importance: Importance;
    summary: string | null;
    created_at: string;
  }[];
}

export interface ReportData {
  period_days: number;
  changes_by_type: Record<string, number>;
  changes_by_importance: Record<string, number>;
  changes_by_competitor: Record<string, number>;
  changes_over_time: { date: string; count: number }[];
}
